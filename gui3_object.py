import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter.filedialog as filedialog
from PIL import Image, ImageTk,ImageOps
import sqlite3
import numpy as np
import cv2
import hashlib
import os

#TODO:SQLAlchemyの移行、スクロールバーの追加、マップ上に点灯モーションの追加、探索機能の追加

class Database_Manager:
    def __init__(self):
        self.conn = sqlite3.connect("database.db")  #データベース(database.db)を生成(インメモリデータベースは:memory:を指定)
        self.cursor = self.conn.cursor()                 #カーソルを生成
        self.init_item_database()

    def init_item_database(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS item(id INTEGER PRIMARY KEY AUTOINCREMENT," \
                                                    "name TEXT," \
                                                    "position TEXT)") # テーブル：itemeを生成(id,name,positionをカラムとする)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS shelf(position TEXT," \
                                                    "x INTEGER," \
                                                    "y INTEGER," \
                                                    "z INTEGER)") # テーブル：shelfを生成(position,x,yをカラムとする)
    
    def convert_table_to_list(self):
        self.cursor.execute("SELECT * FROM item") #テーブルitemを取得
        data = self.cursor.fetchall()   #データをリスト化 
        return data
    
class Application:
    def __init__(self):
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
        button.place(x=90,y=130)
        button.bind("<Button-1>",self.button_clicked)

    def setup_search_window(self):
        self.entry3 = ttk.Entry(self.notebook_search,width=40)
        self.entry3.place(x=100,y=30)
        self.entry3_label = ttk.Label(self.notebook_search,text="キーワード")
        self.entry3_label.place(x=0,y=30)
        self.button2 = ttk.Button(self.notebook_search,text="検索")
        self.button2.place(x=90,y=90)
        self.button2.bind("<Button-1>",self.button2_clicked) 
        option = ["商品番号(id)","商品名","棚番号"]
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

    def button_clicked(self,event): #登録タブ(TODO:9データ以上の表示) 
        try:
            self.array_label_clear(self.label)
        except:
            pass
        value = self.entry1.get()
        position = self.entry2.get()
        #cursor.execute("INSERT INTO item VALUES(1,'りんご','C1')") #id:1,name:りんごのデータを登録
        self.database.cursor.execute("INSERT INTO item(name,position) VALUES(?, ?)",(value,position)) 
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
                    self.search_label = ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]},棚座標：{position_result[0][1]},{position_result[0][2]}")
                else:
                    self.search_label = ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]},棚座標：NULL,NULL")
                    self.search_label.place(x=50,y=150+30)
        else:
            self.search_label = [ttk.Label(self.notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in search_result]
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
            print(f"登録済みのハッシュ値(SHA256):{old_sha256}")
            if old_sha256!= sha_256 and old_sha256 != None:
                print("前回読み込んだファイルと異なるため終了します")
                file.close()
                sha256_file.close()
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
            pil_image = Image.open(image_file).convert('RGB')  #cv2で対応できないファイルを読み込み
        except:
            print("ファイルを正常に読み込めませんでした")
            os.remove("sha256_hash.txt")
            exit()
        self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        self.image_file = image_file
        ##self.image = cv2.imread(image_file)
        
        self.blocks = {}
        self.blocks = self.detect_block()
    
    def edit_image(self,x):
        pil_image = Image.open(self.image_file).convert('RGB')
        self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
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
        self.contours,hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
        i=0
        block_count = 1
        for contour in self.contours:
            if hierarchy[0][i][2] == -1:
                self.blocks[i] = contour
                print("[",block_count,"]","ブロック：",contour[0])
                block_count = block_count + 1
            i=i+1
        print("認識されたブロック数：",len(self.blocks))
        return self.blocks

def main():
    Application()

if __name__ == "__main__":
    main()

