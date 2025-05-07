import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sqlite3

label = []
search_label = []

conn = sqlite3.connect("database.db")  #データベース(database.db)を生成(インメモリデータベースは:memory:を指定)
cursor = conn.cursor()                 #カーソルを生成

def init_item_database():
    cursor.execute("CREATE TABLE IF NOT EXISTS item(id INTEGER PRIMARY KEY AUTOINCREMENT," \
                                                    "name TEXT," \
                                                    "position TEXT)") # テーブル：itemeを生成(id,name,positionをカラムとする)

def init_shelf_database():
    cursor.execute("CREATE TABLE IF NOT EXISTS shelf(position TEXT," \
                                                    "x INTEGER," \
                                                    "y INTEGER)") # テーブル：shelfを生成(position,x,yをカラムとする)

def convert_table_to_list():
    cursor.execute("SELECT * FROM item") #テーブルitemを取得
    data = cursor.fetchall()   #データをリスト化 
    return data

def setup_tab():
    global notebook_register,notebook_search,notebook_register_shelf

    root.title("ウィンドウ")
    root.geometry('600x500')

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
    
def label_clear(label):
    for target_label in label:
        target_label.destroy()

def button_clicked(event): #登録タブ(TODO:9データ以上の表示,任意のxy座標を指定) 
    global label
    label_clear(label)

    value = entry1.get()
    position = entry2.get()
    
    #cursor.execute("INSERT INTO item VALUES(1,'りんご','C1')") #id:1,name:りんごのデータを登録
    cursor.execute("INSERT INTO item(name,position) VALUES(?, ?)",(value,position)) 

    conn.commit()
    items = convert_table_to_list()
    label = [ttk.Label(notebook_register,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in items]

    [label[i].place(x=50,y=150+30*i) for i in range(len(items))]

def button2_clicked(event): #検索タブ
    global search_label
    type = ""
    label_clear(search_label)

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
        search_label = [ttk.Label(notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in search_result]
        [search_label[i].place(x=50,y=150+30*i) for i in range(len(search_result))]
    else:
        search_label = [ttk.Label(notebook_search,text=f"ID:{item[0]},商品名：{item[1]},棚番号：{item[2]}") for item in search_result]
        [search_label[i].place(x=50,y=150+30*i) for i in range(len(search_result))]

def main():
    global root
    root = ttk.Window(themename="flatly")
    init_item_database()
    setup_tab()
    root.mainloop()
    conn.close()

if __name__ == "__main__":
    main()

