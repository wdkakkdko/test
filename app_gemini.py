import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter.filedialog as filedialog
from PIL import Image, ImageTk,ImageOps
import sqlite3
import numpy as np
import cv2
import hashlib
import os
import pandas as pd
import google.generativeai as genai

#注意：Gemini API(gemini-2.0-flash-lite)を利用しているため、1分間で登録するデータ数を30データ以内、一日で登録するデータ数を1500データ以内に抑えること

#TODO:スクロールバーの追加、管理ユーザーの追加、マップの立体化(3Dモデル？)、子のある輪郭の対応

class Database_Manager:
    def __init__(self):
        self.conn = sqlite3.connect("database.db")  #データベース(database.db)を生成(インメモリデータベースは:memory:を指定)
        self.cursor = self.conn.cursor()                 #カーソルを生成
        self.init_item_database()

    def init_item_database(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS item(id INTEGER PRIMARY KEY AUTOINCREMENT," \
                                                    "name TEXT," \
                                                    "position TEXT,"\
                                                    "tag TEXT)") # テーブル：itemを生成(id,name,position,tag1,tag2,tag3をカラムとする)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS shelf(position TEXT," \
                                                    "x INTEGER," \
                                                    "y INTEGER," \
                                                    "z INTEGER)") # テーブル：shelfを生成(position,x,yをカラムとする)
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS secret_tag(name TEXT)") # テーブル：secret_tagを生成(nameをカラムとする)
    
    def convert_table_to_list(self):
        self.cursor.execute("SELECT * FROM item") #テーブルitemを取得
        data = self.cursor.fetchall()   #データをリスト化 
        return data
    
    def convert_tag_table_to_list(self):
        self.cursor.execute("SELECT * FROM secret_tag") #テーブルitemを取得
        data = self.cursor.fetchall()   #データをリスト化 
        return data
    
class Application:
    def __init__(self):

        
        self.GEMINI_API_KEY = "" #Gemini apiのtokenを指定(ダブルクォーテーション内に貼り付け)
        genai.configure(api_key=self.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

        self.label = []
        self.search_label = []
        self.now_register_shelf = False
        self.root = ttk.Window(themename="flatly")
        self.database = Database_Manager()

        self.image_file =  filedialog.askopenfilename(title="イメージファイル(フロアマップ)を選択してください")
        self.integrity_check()

        self.image = Image_Processor(self.image_file)
        
        self.blocks = self.image.blocks

        self.setup_tab()
        self.root.mainloop()
        self.database.conn.close()

    def setup_tab(self):
       self.root.title("商品検索アプリ")
       self.root.geometry('1200x1000')

       self.notebook = ttk.Notebook(self.root)
       self.notebook.pack(fill='both', expand=True)
       self.notebook_register = ttk.Frame(self.notebook)
       self.notebook_register_shelf = ttk.Frame(self.notebook)
       self.notebook_search = ttk.Frame(self.notebook) 
       self.notebook.add(self.notebook_register,text = "商品登録")
       self.notebook.add(self.notebook_register_shelf,text = "棚登録")
       self.notebook.add(self.notebook_search,text = "商品検索")

       self.setup_register_window()
       self.setup_search_window()
       self.setup_register_shelf_window()

       self.notebook.pack(fill='both',anchor="nw")

    def setup_register_window(self):
        self.entry1 = ttk.Entry(self.notebook_register,width=40)
        self.entry1.place(x=100,y=30)
        self.entry1_label = ttk.Label(self.notebook_register,text="商品名")
        self.entry1_label.place(x=0,y=30)
        self.entry2 = ttk.Entry(self.notebook_register,width=40)
        self.entry2.place(x=100,y=80)
        self.entry2_label = ttk.Label(self.notebook_register,text="棚番号")
        self.entry2_label.place(x=0,y=80)

        button = ttk.Button(self.notebook_register,text="決定")
        button.place(x=210,y=130)
        button.bind("<Button-1>",self.button_clicked)
        button_csv = ttk.Button(self.notebook_register,text="CSVを選択")
        button_csv.place(x=90,y=130)
        button_csv.bind("<Button-1>",self.csv_button_clicked)

    def setup_search_window(self):
        self.entry3 = ttk.Entry(self.notebook_search,width=40)
        self.entry3.place(x=100,y=30)
        self.entry3_label = ttk.Label(self.notebook_search,text="キーワード")
        self.entry3_label.place(x=0,y=30)
        self.button2 = ttk.Button(self.notebook_search,text="検索")
        self.button2.place(x=90,y=90)
        self.button2.bind("<Button-1>",self.button2_clicked) 
        option = ["商品番号(id)","商品名","棚番号","キーワード(ジャンル)"]
        self.combobox = ttk.Combobox(self.notebook_search,values=option,state="readonly")
        self.combobox.place(x=300,y=30)

    def setup_register_shelf_window(self):
        self.entry4 = ttk.Entry(self.notebook_register_shelf,width=40)
        self.entry4.place(x=100,y=50)
        self.entry4_label = ttk.Label(self.notebook_register_shelf,text="棚番号")
        self.entry4_label.place(x=20,y=50)
        button = ttk.Button(self.notebook_register_shelf,text="決定")
        button.place(x=100,y=110)
        self.init_label_register_shelf()
        button.bind("<Button-1>",self.button3_clicked) 
        self.canvas = ttk.Canvas(self.notebook_register_shelf,width=1152,height=720)
        self.canvas.place(x=0,y=140)
        self.canvas.bind("<Button-1>",self.canvas_clicked)

    def array_label_clear(self,label):
        for target_label in label:
            target_label.destroy()

    def init_label_register_shelf(self):
        self.label_register_map = ttk.Label(self.notebook_register_shelf,text='棚番号を入力してください')
        self.label_register_map.place(x=100,y=10)

    def gemini_generate_cont(self,value,group):
        self.res = self.model.generate_content("私は現在、ユーザーが入力した商品名をカテゴリごとに分類するアプリを開発しています"\
                                                f"リストで与えられた{value}を各要素ごとに一般的に用いられている固有名詞でグループ分けし、{value}の各要素ごとに3つのグループ名を出力してください。" \
                                                f"既存のグループに組み分けられる場合は既存のグループを用い、組み分けれない場合は新たにグループを作成してください。現在{group}のグループがあります" \
                                                "このときグループ名から商品のジャンルが連想できるように、実在する名称で命名してください。" \
                                                "あなたが出力したコードはpythonを用いて直接databaseに保存するため、回答は必ずグループ名のみを出力し、以下の例にならって出力してください。" \
                                                "入力例:[商品1\n商品2]　出力例:商品1のキーワード1　商品1のキーワード2　商品1のキーワード3,商品2のキーワード1　商品2のキーワード2　商品2のキーワード3"
                                                "より具体的な例としては、[かっぱえびせん,うまい棒]が与えられた際、出力はお菓子　スナック　食べもの,お菓子　スナック　食べものです。"\
                                                "ただし、[かっぱえびせん]が与えられた際は、出力はお菓子　スナック　食べものです"\
                                                "また、[ハーゲンダッツ,あまおう]が与えられた場合、出力はアイスクリーム　デザート　食べもの,いちご　果物　食べものです"\
                                                "ただし以下の制約を守ってください"\
                                                "1.「商品名」という単語が含まれている要素は無視すること"\
                                                "2.数字は無視し、文字列だけを抜き出すこと"\
                                                "3.改行された単語、およびカンマで区切られた単語は異なる名詞であるとみなし、それぞれ各商品にあった適切なワードで名詞ごとにグループ分けすること"\
                                                "4.1単語に付与されるキーワードは必ず3つのみ(2つ以下や4つ以上にしない)にすること"\
                                                "5.グループ名に記号を用いないこと"\
                                                "6.キーワードとカンマ以外の出力を行わないこと"
                                                f"では上記の制約を守り、{value}を分類してください")
        print("キーワード：",self.res.text) ##出力：tag1 tag2 tag3
        print("value：",value)
        list_res = self.res.text.split(',')
        print(list_res)
        non_space_list_res = [tag.strip() for tag in self.res.text.split(',') if tag.strip()]

        in_group = False
        for data in group:
            for output in non_space_list_res:
                if data not in output:
                    self.database.cursor.execute("INSERT INTO secret_tag(name) VALUES(?)",(output,)) 
                    self.database.conn.commit()
        return list_res

    def button_clicked(self,event): #登録タブ(TODO:9データ以上の表示) 
        try:
            self.array_label_clear(self.label)
        except:
            pass

        value = self.entry1.get()
        position = self.entry2.get()
        group = self.database.convert_tag_table_to_list()
        list_res = self.gemini_generate_cont(value,group)


        #cursor.execute("INSERT INTO item VALUES(1,'りんご','C1')") #id:1,name:りんごのデータを登録

        self.database.cursor.execute("INSERT INTO item(name,position,tag) VALUES(?, ?, ?)",(value,position,self.res.text)) 
        self.database.conn.commit()
        items = self.database.convert_table_to_list()
        self.label = [ttk.Label(self.notebook_register,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in items]

        [self.label[i].place(x=50,y=170+30*i) for i in range(len(items))]

    def button2_clicked(self,event): #検索タブ
        type = ""
        try:
            self.array_label_clear(self.search_label)
        except:
            pass
        try:
            self.search_canvas.destroy()
        except:
            pass
        
        keyword = self.entry3.get()
        match self.combobox.current():
            case 0:
                type = "id"
            case 1:
                type = "name"
            case 2:
                type = "position"
            case 3:
                type = "tag"
            case _:
                self.search_label = ttk.Label(self.notebook_search,text="Please specify target.")
                self.search_label.place(x=50,y=150)
                return
        self.database.cursor.execute(f"SELECT * FROM item WHERE {type} LIKE ?",('%'+keyword+'%',))
        search_result = self.database.cursor.fetchall()   #データをリスト化 
        if(len(search_result)==0):
            self.search_label = ttk.Label(self.notebook_search,text="No data found.")
            self.search_label.place(x=50,y=150)
            return
        elif(len(search_result)==1):
            for item in search_result:
                self.database.cursor.execute(f"SELECT * FROM shelf WHERE position = ?",(item[2],))
                position_result = self.database.cursor.fetchall()
                if len(position_result) != 0:
                    self.image.edit_image(position_result[0][1])
                    self.create_canvas()
                    self.search_label = ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}")
                else:
                    self.search_label = ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}")
                    self.search_label.place(x=50,y=150+30)
        else:
            self.search_label = [ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]},tag:{item[3]}") for item in search_result]
            [self.search_label[i].place(x=50,y=150+30*i) for i in range(len(search_result))]

    def create_canvas(self):
        self.search_canvas = ttk.Canvas(self.notebook_search,width=1152,height=720)
        self.search_canvas.place(x=0,y=140)
        pil_image = Image.open("print_image.png")
        #pil_image = ImageOps.pad(pil_image,(800,800))
        self.tk_search_image = ImageTk.PhotoImage(pil_image)
        self.search_canvas.create_image(1152/2,720/2,image=self.tk_search_image)
    
    def button3_clicked(self,event):
        self.select_position = self.entry4.get()
        self.label_register_map.destroy()
        self.label_register_map = ttk.Label(self.notebook_register_shelf,text=f"{self.select_position}の場所を選択してください")
        self.label_register_map.place(x=100,y=10)
        self.print_image()
        self.now_register_shelf = True
    
    def csv_button_clicked(self,event):
        self.csv_file =  filedialog.askopenfilename(title="csvファイルを選択してください")
        group = self.database.convert_tag_table_to_list()
        pd_csv = pd.read_csv(self.csv_file,encoding="shift-jis",sep=",",skip_blank_lines=True)

        pd_csv.columns = pd_csv.columns.str.strip().str.replace('\ufeff', '', regex=False)

        print(pd_csv.columns)
        res_list = self.gemini_generate_cont(list(pd_csv['name']),group)
        list_csv = list(pd_csv)    

        for i in range(len(pd_csv)):
            name = pd_csv.iloc[i, 0]
            position = pd_csv.iloc[i, 1]
            tag = res_list[i]
            self.database.cursor.execute("INSERT INTO item(name,position,tag) VALUES(?, ?, ?)",(name,position,tag)) 
       
        items = self.database.convert_table_to_list()
        self.label = [ttk.Label(self.notebook_register,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in items]
        [self.label[i].place(x=50,y=170+30*i) for i in range(len(items))]
        

    def canvas_clicked(self,event):
        point = (event.x,event.y)
        print(f"clicked:{point}")
        if self.now_register_shelf == True:
            for i in self.blocks:
                contour = self.blocks[i]
                if(cv2.pointPolygonTest(contour,point,False)==1):
                    print("find:",contour[0])
                    self.database.cursor.execute("INSERT INTO shelf(position,x,y,z) VALUES(?, ?, ?, ?)",(self.select_position,int(contour[0][0][0]),int(contour[0][0][1]),0)) 
                    self.database.conn.commit()
                    break
            self.label_register_map.destroy()
            self.label_register_map = ttk.Label(self.notebook_register_shelf,text="登録完了")
            self.label_register_map.place(x=100,y=10)
            self.notebook_register_shelf.after(3000, self.init_label_register_shelf)
            self.now_register_shelf=False

    def print_image(self):
        pil_image = Image.open(self.image_file)
        #pil_image = ImageOps.pad(pil_image,(800,800))
        self.tk_image = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(1152/2,720/2,image=self.tk_image)
    
    def integrity_check(self):
        with open(self.image_file,'rb') as file:
            filedata = file.read()
            sha_256 = hashlib.sha256(filedata).hexdigest() #整合性の確認
            print(f"指定されたファイル: {self.image_file},\nハッシュ値(SHA256):　　　　　{sha_256}")
        try:
            sha256_file = open('sha256_hash.txt',mode='r')
            old_sha256 = sha256_file.read()
            print(f"前回使用したハッシュ値(SHA256):{old_sha256}")
            if old_sha256!= sha_256 and old_sha256 != None:
                print("前回読み込んだファイルと異なるため終了します")
                file.close()
                sha256_file.close()
                os.remove('sha256_hash.txt')
                self.exit_window()
        except:
            sha256_file = open('sha256_hash.txt',mode='a')
            sha256_file.write(str(sha_256))

        file.close()
        sha256_file.close()

    def exit_window(self):
        self.root.quit()
        self.root.destroy()
        self.database.conn.close()
        exit()

class Image_Processor:
    def __init__(self,image_file):
        try:
            self.pil_image = Image.open(image_file).convert('RGB')  #cv2で対応できないファイルを読み込み
        except:
            print("ファイルを正常に読み込めませんでした")
            os.remove("sha256_hash.txt")
            exit()
        self.image = cv2.cvtColor(np.array(self.pil_image), cv2.COLOR_RGB2BGR)
        self.image_file = image_file
        ##self.image = cv2.imread(image_file)
        
        self.blocks = {}
        self.blocks = self.detect_block()
    
    def edit_image(self,x):
        self.image = cv2.cvtColor(np.array(self.pil_image), cv2.COLOR_RGB2BGR)
        for i in self.blocks:
            contours = self.blocks[i]
            if contours[0][0][0] == x:
                print("block:",contours[0][0][0])
                break
        block = {0:contours}
        cv2.drawContours(self.image, list(block.values()), -1, (3, 0, 255), thickness=cv2.FILLED)
        cv2.imwrite(r'print_image.png', self.image)

    def detect_block(self):
        upper = np.array([0,0,0]) #HSVの上限値を設定(黒)
        lower = np.array([0,0,0])
        hsv_image = cv2.cvtColor(self.image,cv2.COLOR_BGR2HSV_FULL)
        mask = cv2.inRange(hsv_image,lower,upper)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)

        self.contours,hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
        i=0
        block_count = 1
        for contour in self.contours:
            if hierarchy[0][i][2] == -1:
                area = cv2.contourArea(contour)
                if area < 10:  # 面積が小さいものは無視
                   continue
                self.blocks[i] = contour
                top_left = min(contour, key=lambda point: point[0][0] + point[0][1])
                print("[",block_count,"]","ブロックの一点：",contour[0])
                block_count = block_count + 1
            i=i+1
        print("認識されたブロック数：",len(self.blocks))
        return self.blocks

def main():
    Application()

if __name__ == "__main__":
    main()

