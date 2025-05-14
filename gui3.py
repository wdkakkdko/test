import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk,ImageOps
import sqlite3
import numpy as np
import cv2


label = []
search_label = []
blocks = {}
now_register_shelf = False


conn = sqlite3.connect("database.db")  #データベース(database.db)を生成(インメモリデータベースは:memory:を指定)
cursor = conn.cursor()                 #カーソルを生成

def init_item_database():
    cursor.execute("CREATE TABLE IF NOT EXISTS item(id INTEGER PRIMARY KEY AUTOINCREMENT," \
                                                    "name TEXT," \
                                                    "position TEXT)") # テーブル：itemeを生成(id,name,positionをカラムとする)

def init_shelf_database():
    cursor.execute("CREATE TABLE IF NOT EXISTS shelf(position TEXT," \
                                                    "x INTEGER," \
                                                    "y INTEGER," \
                                                    "z INTEGER)") # テーブル：shelfを生成(position,x,yをカラムとする)

def convert_table_to_list():
    cursor.execute("SELECT * FROM item") #テーブルitemを取得
    data = cursor.fetchall()   #データをリスト化 
    return data

def setup_tab():
    global notebook_register,notebook_search,notebook_register_shelf

    root.title("ウィンドウ")
    root.geometry('1200x1000')

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    notebook_register = ttk.Frame(notebook)
    notebook_register_shelf = ttk.Frame(notebook)
    notebook_search = ttk.Frame(notebook) 
    notebook.add(notebook_register,text = "商品登録")
    notebook.add(notebook_register_shelf,text = "棚登録")
    notebook.add(notebook_search,text = "商品検索")

    setup_register_window()
    setup_search_window()
    setup_register_shelf_window()
    notebook.pack(fill='both',anchor="nw")

def setup_register_window():
    global entry1,entry2,button

    entry1 = ttk.Entry(notebook_register,width=40)
    entry1.place(x=100,y=30)
    entry1_label = ttk.Label(notebook_register,text="商品名")
    entry1_label.place(x=0,y=30)
    entry2 = ttk.Entry(notebook_register,width=40)
    entry2.place(x=100,y=80)
    entry2_label = ttk.Label(notebook_register,text="棚番号")
    entry2_label.place(x=0,y=80)
    button = ttk.Button(notebook_register,text="決定")
    button.place(x=90,y=130)
    button.bind("<Button-1>",button_clicked) 

def setup_search_window():
    global entry3,button2,combobox

    entry3 = ttk.Entry(notebook_search,width=40)
    entry3.place(x=100,y=30)
    entry3_label = ttk.Label(notebook_search,text="キーワード")
    entry3_label.place(x=0,y=30)
    button2 = ttk.Button(notebook_search,text="検索")
    button2.place(x=90,y=90)
    button2.bind("<Button-1>",button2_clicked) 
    option = ["商品番号(id)","商品名","棚番号"]
    combobox = ttk.Combobox(notebook_search,values=option,state="readonly")
    combobox.place(x=300,y=30)

def setup_register_shelf_window():
    global entry4,button,canvas

    entry4 = ttk.Entry(notebook_register_shelf,width=40)
    entry4.place(x=100,y=50)
    entry4_label = ttk.Label(notebook_register_shelf,text="棚番号")
    entry4_label.place(x=20,y=50)
    button = ttk.Button(notebook_register_shelf,text="決定")
    button.place(x=100,y=110)
    init_label_register_shelf()
    button.bind("<Button-1>",button3_clicked) 
    canvas = ttk.Canvas(notebook_register_shelf,width=1152,height=720)
    canvas.place(x=0,y=140)
    canvas.bind("<Button-1>",canvas_clicked)


def array_label_clear(label):
    print(len(label))
    for target_label in label:
        target_label.destroy()

def init_label_register_shelf():
    global label_register_map
    label_register_map = ttk.Label(notebook_register_shelf,text='棚番号を入力してください')
    label_register_map.place(x=100,y=10)

def button_clicked(event): #登録タブ(TODO:9データ以上の表示,任意のxy座標を指定) 
    global label
    try:
       array_label_clear(label)
    except:
        pass

    value = entry1.get()
    position = entry2.get()
    
    #cursor.execute("INSERT INTO item VALUES(1,'りんご','C1')") #id:1,name:りんごのデータを登録
    cursor.execute("INSERT INTO item(name,position) VALUES(?, ?)",(value,position)) 
    conn.commit()
    items = convert_table_to_list()
    label = [ttk.Label(notebook_register,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in items]

    [label[i].place(x=50,y=170+30*i) for i in range(len(items))]

def button2_clicked(event): #検索タブ
    global search_label,search_canvas
    type = ""
    
    try:
       array_label_clear(search_label)
    except:
        pass

    try:
        search_canvas.destroy()
        print("destroy")
    except:
        pass
    keyword = entry3.get()

    match combobox.current():
        case 0:
            type = "id"
        case 1:
            type = "name"
        case 2:
            type = "position"
        case _:
            search_label = ttk.Label(notebook_search,text="Please specify target.")
            search_label.place(x=50,y=150)
            return
    
    cursor.execute(f"SELECT * FROM item WHERE {type} LIKE ?",('%'+keyword+'%',))

    search_result = cursor.fetchall()   #データをリスト化 


    if(len(search_result)==0):
        search_label = ttk.Label(notebook_search,text="No data found.")
        search_label.place(x=50,y=150)
        return
    elif(len(search_result)==1):
        #TODO:フロアマップを表示し、ロケーションを強調表示
        for item in search_result:
            cursor.execute(f"SELECT * FROM shelf WHERE position = ?",(item[2],))
            position_result = cursor.fetchall()
            print(position_result)
            if len(position_result) != 0:
                edit_image(position_result[0][1])
                create_canvas()
                search_label = ttk.Label(notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]},棚座標：{position_result[0][1]},{position_result[0][2]}")
            else:
                search_label = ttk.Label(notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]},棚座標：NULL,NULL")
            search_label.place(x=50,y=150+30)
    else:
        search_label = [ttk.Label(notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in search_result]
        [search_label[i].place(x=50,y=150+30*i) for i in range(len(search_result))]

def create_canvas():
    global tk_search_image,search_canvas
    search_canvas = ttk.Canvas(notebook_search,width=1152,height=720)
    search_canvas.place(x=0,y=140)
    pil_image = Image.open("print_image.png")
    #pil_image = ImageOps.pad(pil_image,(800,800))
    tk_search_image = ImageTk.PhotoImage(pil_image)
    
    search_canvas.create_image(1152/2,720/2,image=tk_search_image)

def edit_image(x):
    global target_image
    target_image = cv2.imread('test3.png')
    for i in blocks:
        contours = blocks[i]
        if contours[0][0][0] == x:
            print("block:",contours[0][0][0])
            break
    print(len(contours))
    block = {0:contours}
    cv2.drawContours(target_image, list(block.values()), -1, (3, 0, 255), thickness=cv2.FILLED)
    cv2.imwrite(r'print_image.png', target_image)
    

def button3_clicked(event):
    global label_register_map,select_position,now_register_shelf
    select_position = entry4.get()
    label_register_map.destroy()
    label_register_map = ttk.Label(notebook_register_shelf,text=f"{select_position}の場所を選択してください")
    label_register_map.place(x=100,y=10)
    print_image()
    now_register_shelf = True

def canvas_clicked(event):
    global now_register_shelf,label_register_map

    point = (event.x,event.y)
    print(f"clicked:{point}")
    if now_register_shelf == True:
        for i in blocks:
            contour = blocks[i]
            if(cv2.pointPolygonTest(contour,point,False)==1):
                print("find:",contour[0])
                cursor.execute("INSERT INTO shelf(position,x,y,z) VALUES(?, ?, ?, ?)",(select_position,int(contour[0][0][0]),int(contour[0][0][1]),0)) 
                conn.commit()
                break
        label_register_map.destroy()

        label_register_map = ttk.Label(notebook_register_shelf,text="登録完了")
        label_register_map.place(x=100,y=10)

        notebook_register_shelf.after(3000, init_label_register_shelf)
        now_register_shelf=False

def print_image():
    global tk_image
    pil_image = Image.open("test3.png")
    #pil_image = ImageOps.pad(pil_image,(800,800))
    tk_image = ImageTk.PhotoImage(pil_image)
    
    canvas.create_image(1152/2,720/2,image=tk_image)
    

def setup_image():
    global image,blocks
    image = cv2.imread('test3.png')

    upper = np.array([0,0,0]) #HSVの上限値を設定(黒)
    lower = np.array([0,0,0])
    hsv_image = cv2.cvtColor(image,cv2.COLOR_BGR2HSV_FULL)
    mask = cv2.inRange(hsv_image,lower,upper)
    contours,hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    i=0
    for contour in contours:
        if hierarchy[0][i][2] == -1:
            blocks[i] = contour
            print(contour[0])
        i=i+1

    print(len(blocks))


def main():
    global root
    root = ttk.Window(themename="flatly")
    init_item_database()
    init_shelf_database()
    setup_image()
    setup_tab()
    root.mainloop()
    conn.close()

if __name__ == "__main__":
    main()

