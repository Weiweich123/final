import requests
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import render_template

# 初始化 Flask 應用程式
app = Flask(__name__)
# 設定資料庫 URI 和追蹤修改的參數
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 初始化 SQLAlchemy
db = SQLAlchemy(app)

# 設備模型
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主鍵
    name = db.Column(db.String(50), nullable=False)  # 設備名稱
    status = db.Column(db.String(20), nullable=False, default="available")  # 設備狀態（"available" 或 "in-use"）
    usage_count = db.Column(db.Integer, default=0)  # 設備使用次數

# 預約模型
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主鍵
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)  # 對應設備的外鍵
    user = db.Column(db.String(50), nullable=False)  # 使用者名稱
    time_slot = db.Column(db.String(50), nullable=False)  # 預約時間段

# 建立資料表
with app.app_context():
    db.create_all()

# 查詢所有設備的 API
@app.route('/equipment', methods=['GET'])
def get_equipment():
    equipment_list = Equipment.query.all()  # 查詢所有設備
    return jsonify([
        {"id": eq.id, "name": eq.name, "status": eq.status, "usage_count": eq.usage_count}
        for eq in equipment_list
    ])

# 預約設備的 API
@app.route('/reserve', methods=['POST'])
def reserve_equipment():
    data = request.json  # 取得請求的 JSON 資料
    equipment = Equipment.query.get(data['equipment_id'])  # 根據 ID 查詢設備

    # 檢查設備是否可用
    if equipment and equipment.status == "available":
        # 創建預約記錄
        reservation = Reservation(
            equipment_id=equipment.id,
            user=data['user'],
            time_slot=data['time_slot']
        )
        db.session.add(reservation)

        # 更新設備狀態和使用次數
        equipment.status = "in-use"
        equipment.usage_count += 1
        db.session.commit()

        return jsonify({"message": "Reservation successful"})
    return jsonify({"message": "Equipment not available"}), 400

# 釋放設備的 API
@app.route('/release/<int:equipment_id>', methods=['POST'])
def release_equipment(equipment_id):
    equipment = Equipment.query.get(equipment_id)  # 根據 ID 查詢設備
    # 檢查設備是否處於使用狀態
    if equipment and equipment.status == "in-use":
        equipment.status = "available"  # 更新設備狀態為可用
        db.session.commit()
        return jsonify({"message": "Equipment released successfully"})
    return jsonify({"message": "Equipment not in use"}), 400

# 添加設備的 API
@app.route('/add-equipment', methods=['POST'])
def add_equipment():
    data = request.json  # 取得請求的 JSON 資料
    new_equipment = Equipment(name=data['name'])  # 創建新設備
    db.session.add(new_equipment)
    db.session.commit()
    return jsonify({"message": f"Equipment {data['name']} added"})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-student-report/<string:student_name>', methods=['GET'])
def generate_student_report(student_name):
    # 查詢該學生的預約紀錄
    reservations = Reservation.query.filter_by(user=student_name).all()

    report = {
        'student': student_name,
        'total_reservations': len(reservations),
        'equipment_used': [],
    }

    for reservation in reservations:
        equipment = Equipment.query.get(reservation.equipment_id)
        report['equipment_used'].append({
            'equipment_name': equipment.name,
            'time_slot': reservation.time_slot,
        })

    return jsonify(report)

# 用於批量插入設備的函數
def add_mock_equipment():
    with app.app_context():
        equipment_list = [
            {"name": "Treadmill"},
            {"name": "Exercise Bike"},
            {"name": "Rowing Machine"},
            {"name": "Dumbbells"},
            {"name": "Squat Rack"},
            {"name": "Elliptical Trainer"}
        ]

        for equipment in equipment_list:
            new_equipment = Equipment(name=equipment['name'])
            db.session.add(new_equipment)
        db.session.commit()

if __name__ == '__main__':
    # 啟動 Flask 應用程序
    app.run(debug=False, use_reloader=False)

    # 手動執行模擬數據插入
    add_mock_equipment()
