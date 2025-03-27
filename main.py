from flask import Flask
from routes.login import auth_routes
from routes.db_test import db_routes
from routes.JWT_API import protected_routes
from flask import Flask, request, jsonify
import pyodbc
from datetime import datetime
from config import DB

app = Flask(__name__)


# 註冊藍圖（Blueprint）
app.register_blueprint(auth_routes)
app.register_blueprint(db_routes)
app.register_blueprint(protected_routes)

@app.route('/')
def home():
    return {"message": "Hello, Flask API is running!"}

#申請借用教室
@app.route('/api/borrow', methods=['POST'])
def borrow_classroom():
    try:
        data = request.get_json()
        print("收到的 JSON:", data)

        sid = data.get('sid', None) #學號
        cid = data.get('cid', None) #教室編號
        departments = data.get('departments', None) #科系
        borrow_numbers = data.get('borrow_numbers', None) #借用人數
        borrow_reason = data.get('borrow_reason', None) #借用節數
        start_date = data.get('start_date', None) #開始時間
        end_date = data.get('end_date', None) #結束時間
        borrow_section = data.get('borrow_section', None) #使用說明


        if not all([sid, cid, departments, borrow_numbers, borrow_reason, start_date]):
            return jsonify({"message": "借用失敗，缺少必要參數"}), 400
        
        conn_str = f"DRIVER={{SQL Server}};SERVER={DB['server']},{DB['port']};DATABASE={DB['database']};UID={DB['username']};PWD={DB['password']}"

        db = pyodbc.connect(conn_str)
        cursor = db.cursor()
        print("資料庫連接成功")
        sql = """
            INSERT INTO NHU_CST.dbo.borrow (
                sid, cid, departments, borrow_numbers, borrow_reason, 
                start_date, end_date, borrow_section, created_at, is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        is_approved = 0
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        values = (sid, cid, departments, borrow_numbers, borrow_reason, start_date, end_date, borrow_section, created_at, is_approved)
        cursor.execute(sql, values)
        db.commit()
        cursor.close()

        return jsonify({"message": "借用成功"}), 201
    except Exception as e:
        return jsonify({"message": f"借用失敗，錯誤：{str(e)}"}), 500
    
#顯示可借教室
@app.route('/api/remainclass')

def remain_class():
    try:
        name = request.args.get('name')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if not name or not start_time or not end_time:
            return jsonify({"message": "請提供完整的查詢參數"}), 400
        
        start_dt = datetime.strptime(start_time, "%Y-%m-%d")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d")

        delta_days = (end_dt - start_dt).days

        one_month_days = 30

        conn_str = f"DRIVER={{SQL Server}};SERVER={DB['server']},{DB['port']};DATABASE={DB['database']};UID={DB['username']};PWD={DB['password']}"

        db = pyodbc.connect(conn_str)
        cursor = db.cursor()
        print("資料庫連接成功")

        if delta_days <= one_month_days:
            weekday_name = start_dt.strftime("%A")
            sql = f"SELECT {weekday_name} FROM NHU_CST.dbo.classrooms WHERE name = ?"

        else:

            sql = f"SELECT * FROM NHU_CST.dbo.classrooms WHERE name = ?"

        cursor.execute(sql, (name,))
        result = cursor.fetchall()
        result_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in result]

        cursor.close()
        db.close()

        if result_dict:
            return jsonify({"result": result_dict}), 200
        else:
            return jsonify({"message": "未找到符合條件的資料"}), 404
        
    except Exception as e:
        # 若發生錯誤，返回詳細錯誤信息
        return jsonify({"message": f"借用查詢失敗，錯誤：{str(e)}"}), 500
        

@app.route('/api/borrow_data')
def borrow_data():
    conn_str = f"DRIVER={{SQL Server}};SERVER={DB['server']},{DB['port']};DATABASE={DB['database']};UID={DB['username']};PWD={DB['password']}"
    db = pyodbc.connect(conn_str)
    cursor = db.cursor()
    print("資料庫連接成功")
    sql = f"SELECT *FROM [NHU_CST].[dbo].[borrow]"
    cursor.execute(sql)
    result = cursor.fetchall()
    result_dict = [dict(zip([column[0] for column in cursor.description], row)) for row in result]

    cursor.close()
    db.close()

    return result_dict
if __name__ == '__main__':
    app.run(debug=True)

