"""
ETL Pipeline & Question Bank Seeder
Extracts raw HSK examination records, transforms & validates schemas,
and loads them into the relational SQLite database.
"""

import json
import sqlite3
from typing import List, Dict, Any
from app.database import get_connection, init_db

# Comprehensive HSK Questions Dataset (HSK 1, HSK 2, HSK 3)
RAW_QUESTIONS: List[Dict[str, Any]] = [
    # ==================== HSK 1 Questions ====================
    {
        "level": 1,
        "part": "คำศัพท์",
        "question": "苹果 (píngguǒ) แปลว่าอะไร?",
        "pinyin": "píngguǒ",
        "translation": "แอปเปิ้ล",
        "options": ["กล้วย", "แอปเปิ้ล", "ส้ม", "มะม่วง"],
        "correct_answer": "แอปเปิ้ล",
        "explanation": "苹果 (píngguǒ) เป็นคำนามพื้นฐานใน HSK 1 หมายถึง 'แอปเปิ้ล'"
    },
    {
        "level": 1,
        "part": "คำศัพท์",
        "question": "汉语 (Hànyǔ) แปลว่าอะไร?",
        "pinyin": "Hànyǔ",
        "translation": "ภาษาจีน",
        "options": ["ภาษาเกาหลี", "ภาษาญี่ปุ่น", "ภาษาอังกฤษ", "ภาษาจีน"],
        "correct_answer": "ภาษาจีน",
        "explanation": "汉语 (Hànyǔ) หมายถึง 'ภาษาจีน' (汉 = ชาวฮั่น, 语 = ภาษา)"
    },
    {
        "level": 1,
        "part": "คำศัพท์",
        "question": "谢谢 (xièxie) แปลว่าอะไร?",
        "pinyin": "xièxie",
        "translation": "ขอบคุณ",
        "options": ["ขอบคุณ", "ขอโทษ", "ลาก่อน", "ไม่เป็นไร"],
        "correct_answer": "ขอบคุณ",
        "explanation": "谢谢 (xièxie) แปลว่า 'ขอบคุณ' คำตอบรับที่สุภาพคือ 不客气 (bú kèqi)"
    },
    {
        "level": 1,
        "part": "คำศัพท์",
        "question": "猫 (māo) แปลว่าสัตว์ชนิดใด?",
        "pinyin": "māo",
        "translation": "แมว",
        "options": ["สุนัข", "แมว", "นก", "ปลา"],
        "correct_answer": "แมว",
        "explanation": "猫 (māo) หมายถึง 'แมว' ส่วนสุนัขคือ 狗 (gǒu)"
    },
    {
        "level": 1,
        "part": "ไวยากรณ์",
        "question": "จงเติมคำในช่องว่าง: 他是我的老师______？ (เขาเป็นคุณครูของฉันใช่ไหม?)",
        "pinyin": "Tā shì wǒ de lǎoshī ______?",
        "translation": "เขาเป็นคุณครูของฉันใช่ไหม?",
        "options": ["吗 (ma)", "呢 (ne)", "了 (le)", "的 (de)"],
        "correct_answer": "吗 (ma)",
        "explanation": "吗 (ma) เป็นคำลงท้ายประโยคคำถามแบบ Yes/No Question ในภาษาจีน"
    },
    {
        "level": 1,
        "part": "ไวยากรณ์",
        "question": "ประโยคใดเรียงลำดับประธาน-กริยา-กรรมถูกต้อง?",
        "pinyin": "Wǒ chī mǐfàn.",
        "translation": "ฉันกินข้าวสวย",
        "options": ["我吃米饭", "米饭吃我", "吃我米饭", "我米饭吃"],
        "correct_answer": "我吃米饭",
        "explanation": "โครงสร้างไวยากรณ์พื้นฐานภาษาจีนคือ ประธาน (我) + กริยา (吃) + กรรม (米饭)"
    },
    {
        "level": 1,
        "part": "ตัวเลขและเวลา",
        "question": "星期三 (xīngqīsān) คือวันอะไร?",
        "pinyin": "xīngqīsān",
        "translation": "วันพุธ",
        "options": ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี"],
        "correct_answer": "วันพุธ",
        "explanation": "星期一 = วันจันทร์, 星期二 = วันอังคาร, 星期三 = วันพุธ"
    },
    {
        "level": 1,
        "part": "ตัวเลขและเวลา",
        "question": "九月 (jiǔ yuè) คือเดือนอะไร?",
        "pinyin": "jiǔ yuè",
        "translation": "เดือนกันยายน",
        "options": ["เดือนสิงหาคม", "เดือนกันยายน", "เดือนตุลาคม", "เดือนพฤศจิกายน"],
        "correct_answer": "เดือนกันยายน",
        "explanation": "九 (jiǔ) แปลว่า 9, 月 (yuè) แปลว่า เดือน ดังนั้น 九月 คือเดือนกันยายน"
    },
    {
        "level": 1,
        "part": "การอ่านและการสนทนา",
        "question": "A: 对不起！ (ขอโทษนะ!) — B ควรตอบว่าอย่างไร?",
        "pinyin": "A: Duìbuqǐ! — B: ______",
        "translation": "A: ขอโทษครับ! — B: ไม่เป็นไรครับ",
        "options": ["没关系 (méi guānxi)", "不客气 (bú kèqi)", "再见 (zàijiàn)", "很好 (hěn hǎo)"],
        "correct_answer": "没关系 (méi guānxi)",
        "explanation": "เมื่อมีคนพูดว่า 对不起 (ขอโทษ) การตอบรับตามมารยาทคือ 没关系 (ไม่เป็นไร)"
    },
    {
        "level": 1,
        "part": "การอ่านและการสนทนา",
        "question": "你叫什么名字？ (Nǐ jiào shénme míngzi?) มีความหมายตรงกับข้อใด?",
        "pinyin": "Nǐ jiào shénme míngzi?",
        "translation": "คุณชื่ออะไร?",
        "options": ["คุณอายุเท่าไหร่?", "คุณชื่ออะไร?", "คุณมาจากที่ไหน?", "คุณสบายดีไหม?"],
        "correct_answer": "คุณชื่ออะไร?",
        "explanation": "你 (คุณ) + 叫 (ชื่อว่า/เรียก) + 什么 (อะไร) + 名字 (ชื่อ) = คุณชื่ออะไร?"
    },

    # ==================== HSK 2 Questions ====================
    {
        "level": 2,
        "part": "คำศัพท์",
        "question": "机场 (jīchǎng) แปลว่าสถานที่ใด?",
        "pinyin": "jīchǎng",
        "translation": "สนามบิน",
        "options": ["สถานีรถไฟ", "โรงพยาบาล", "สนามบิน", "โรงภาพยนตร์"],
        "correct_answer": "สนามบิน",
        "explanation": "机场 (jīchǎng) หมายถึง สนามบิน (机 = เครื่องบิน, 场 = ลาน/สถานที่)"
    },
    {
        "level": 2,
        "part": "คำศัพท์",
        "question": "便宜 (piányi) มีความหมายตรงข้ามกับคำว่าอะไร?",
        "pinyin": "piányi",
        "translation": "ราคาถูก",
        "options": ["贵 (guì - แพง)", "快 (kuài - เร็ว)", "高 (gāo - สูง)", "新 (xīn - ใหม่)"],
        "correct_answer": "贵 (guì - แพง)",
        "explanation": "便宜 (piányi) แปลว่า 'ราคาถูก' ตรงข้ามกับ 贵 (guì) ที่แปลว่า 'แพง'"
    },
    {
        "level": 2,
        "part": "คำศัพท์",
        "question": "服务员 (fúwùyuán) คืออาชีพใด?",
        "pinyin": "fúwùyuán",
        "translation": "พนักงานบริการ / บริกร",
        "options": ["คุณครู", "แพทย์", "พนักงานบริการ", "คนขับรถ"],
        "correct_answer": "พนักงานบริการ",
        "explanation": "服务员 (fúwùyuán) แปลว่า พนักงานบริการหรือบริกรในร้านอาหาร/โรงแรม"
    },
    {
        "level": 2,
        "part": "ไวยากรณ์",
        "question": "จงเลือกประโยคเปรียบเทียบที่ถูกต้อง: 'เขาตัวสูงกว่าฉัน'",
        "pinyin": "Tā bǐ wǒ gāo.",
        "translation": "เขาตัวสูงกว่าฉัน",
        "options": ["他比我高", "他和我高", "他最我高", "我比他高"],
        "correct_answer": "他比我高",
        "explanation": "ไวยากรณ์เปรียบเทียบ HSK 2: A + 比 + B + คุณศัพท์ -> 他 (เขา) + 比 + 我 (ฉัน) + 高 (สูง)"
    },
    {
        "level": 2,
        "part": "ไวยากรณ์",
        "question": "จงเติมคำสันธาน: ______今天下雨，______我们不去踢足球了。",
        "pinyin": "______ jīntiān xià yǔ, ______ wǒmen bú qù tī zúqiú le.",
        "translation": "เพราะว่าวันนี้ฝนตก ดังนั้นพวกเราจึงไม่ไปเตะฟุตบอล",
        "options": [
            "因为...所以... (เพราะว่า...ดังนั้น...)",
            "虽然...但是... (แม้ว่า...แต่ว่า...)",
            "不仅...而且... (ไม่เพียงแต่...อีกทั้งยัง...)",
            "如果...就... (ถ้าหาก...ก็...)"
        ],
        "correct_answer": "因为...所以... (เพราะว่า...ดังนั้น...)",
        "explanation": "因为 (เพราะว่า) บอกสาเหตุ คู่กับ 所以 (ดังนั้น) บอกผลลัพธ์ เป็นไวยากรณ์หลักของ HSK 2"
    },
    {
        "level": 2,
        "part": "ตัวเลขและเวลา",
        "question": "两点半 (liǎng diǎn bàn) คือเวลาใด?",
        "pinyin": "liǎng diǎn bàn",
        "translation": "บ่ายสองโมงครึ่ง (02:30 / 14:30)",
        "options": ["02:00", "02:15", "02:30", "03:30"],
        "correct_answer": "02:30",
        "explanation": "两点 = 2 โมง, 半 = ครึ่ง (30 นาที) จึงหมายถึง เวลาสองโมงครึ่ง"
    },
    {
        "level": 2,
        "part": "ตัวเลขและเวลา",
        "question": "คำลักษณนามสำหรับ 'เสื้อผ้า (衣服)' ใน HSK 2 คือคำใด?",
        "pinyin": "yīfu liàngcí",
        "translation": "ลักษณนามของเสื้อผ้า",
        "options": ["件 (jiàn)", "本 (běn)", "张 (zhāng)", "条 (tiáo)"],
        "correct_answer": "件 (jiàn)",
        "explanation": "一件衣服 (yí jiàn yīfu) คำว่า 件 ใช้เป็นลักษณนามของเสื้อผ้าและเรื่องราว"
    },
    {
        "level": 2,
        "part": "การอ่านและการสนทนา",
        "question": "A: 你累了吗？ (คุณเหนื่อยหรือยัง?) — B ควรตอบว่าอย่างไร?",
        "pinyin": "A: Nǐ lèi le ma? — B: ______",
        "translation": "A: คุณเหนื่อยหรือยัง? — B: เหนื่อยแล้ว พวกเราพักผ่อนสักหน่อยเถอะ",
        "options": [
            "累了，我们休息一下吧 (เหนื่อยแล้ว พักสักหน่อยเถอะ)",
            "我不认识他 (ฉันไม่รู้จักเขา)",
            "明天见 (เจอกันพรุ่งนี้)",
            "这个很便宜 (อันนี้ถูกมาก)"
        ],
        "correct_answer": "累了，我们休息一下吧 (เหนื่อยแล้ว พักสักหน่อยเถอะ)",
        "explanation": "ตอบตรงคำถามเรื่องความเหนื่อย โดยเสนอให้ 休息 (พักผ่อน)"
    },

    # ==================== HSK 3 Questions ====================
    {
        "level": 3,
        "part": "คำศัพท์",
        "question": "聪明 (cōngming) มีความหมายตรงกับข้อใด?",
        "pinyin": "cōngming",
        "translation": "ฉลาด / หัวดี",
        "options": ["ขยัน", "ฉลาด", "ใจดี", "สุภาพ"],
        "correct_answer": "ฉลาด",
        "explanation": "聪明 (cōngming) แปลว่า ฉลาด มีไหวพริบ"
    },
    {
        "level": 3,
        "part": "คำศัพท์",
        "question": "照顾 (zhàogù) หมายถึงกริยาใด?",
        "pinyin": "zhàogù",
        "translation": "ดูแล / เอาใจใส่",
        "options": ["ดูแล", "ซื้อของ", "เดินทาง", "ทำอาหาร"],
        "correct_answer": "ดูแล",
        "explanation": "照顾 (zhàogù) เช่น 照顾生病的人 (ดูแลคนป่วย)"
    },
    {
        "level": 3,
        "part": "ไวยากรณ์",
        "question": "ประโยคที่ใช้โครงสร้าง 把 (bǎ) ข้อใดถูกต้อง?",
        "pinyin": "bǎ zì jù",
        "translation": "ประโยคโครงสร้าง 把",
        "options": [
            "我把作业做完了 (ฉันทำการบ้านเสร็จแล้ว)",
            "我把做完作业了",
            "作业把我做完了",
            "把做完了我作业"
        ],
        "correct_answer": "我把作业做完了 (ฉันทำการบ้านเสร็จแล้ว)",
        "explanation": "โครงสร้างประโยค 把: ประธาน (我) + 把 + กรรม (作业) + กริยา (做) + ผลลัพธ์ (完了)"
    },
    {
        "level": 3,
        "part": "ตัวเลขและเวลา",
        "question": "差一刻八点 (chà yí kè bā diǎn) คือเวลาใด?",
        "pinyin": "chà yí kè bā diǎn",
        "translation": "อีก 15 นาทีแปดโมง (07:45)",
        "options": ["08:15", "07:45", "08:45", "07:15"],
        "correct_answer": "07:45",
        "explanation": "差 (ขาดอีก) + 一刻 (15 นาที) + 八点 (8 โมง) = อีก 15 นาทีแปดโมง หรือ 07:45"
    }
]

def run_etl() -> int:
    """Executes the ETL pipeline: initializes DB, cleanses data, and loads questions."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clean previous table content for fresh reload
    cursor.execute("DELETE FROM questions;")
    
    loaded_count = 0
    for item in RAW_QUESTIONS:
        # Validate data integrity
        options = item["options"]
        correct_answer = item["correct_answer"]
        if correct_answer not in options:
            raise ValueError(f"Correct answer '{correct_answer}' not in options {options} for question: {item['question']}")
        
        cursor.execute("""
            INSERT INTO questions (
                level, part, question, pinyin, translation, options, correct_answer, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["level"],
            item["part"],
            item["question"],
            item.get("pinyin", ""),
            item.get("translation", ""),
            json.dumps(options, ensure_ascii=False),
            correct_answer,
            item.get("explanation", "")
        ))
        loaded_count += 1
        
    conn.commit()
    conn.close()
    return loaded_count

def seed_sample_analytics_history() -> None:
    """Seeds realistic historical attempts so analytics & graphs are immediately demonstrative."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if attempts already exist
    cursor.execute("SELECT COUNT(*) FROM exam_attempts")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    sample_attempts = [
        {
            "level": 1,
            "score": 6,
            "total": 8,
            "percentage": 75.0,
            "time_spent": 142,
            "parts": {"คำศัพท์": [3, 4], "ไวยากรณ์": [1, 2], "ตัวเลขและเวลา": [2, 2]},
            "date": "2026-10-28 14:20:00"
        },
        {
            "level": 1,
            "score": 7,
            "total": 8,
            "percentage": 87.5,
            "time_spent": 128,
            "parts": {"คำศัพท์": [4, 4], "ไวยากรณ์": [1, 2], "ตัวเลขและเวลา": [2, 2]},
            "date": "2026-10-29 16:45:00"
        },
        {
            "level": 1,
            "score": 8,
            "total": 8,
            "percentage": 100.0,
            "time_spent": 95,
            "parts": {"คำศัพท์": [4, 4], "ไวยากรณ์": [2, 2], "ตัวเลขและเวลา": [2, 2]},
            "date": "2026-10-31 10:15:00"
        },
        {
            "level": 2,
            "score": 6,
            "total": 8,
            "percentage": 75.0,
            "time_spent": 165,
            "parts": {"คำศัพท์": [3, 3], "ไวยากรณ์": [1, 3], "ตัวเลขและเวลา": [2, 2]},
            "date": "2026-11-01 19:30:00"
        }
    ]

    for att in sample_attempts:
        cursor.execute("""
            INSERT INTO exam_attempts (
                user_id, level, score, total, percentage, time_spent_seconds, parts, answers_detail, created_at
            ) VALUES ('guest', ?, ?, ?, ?, ?, ?, '[]', ?)
        """, (
            att["level"],
            att["score"],
            att["total"],
            att["percentage"],
            att["time_spent"],
            json.dumps(att["parts"], ensure_ascii=False),
            att["date"]
        ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    count = run_etl()
    print(f"ETL completed! Loaded {count} HSK questions into database.")
    seed_sample_analytics_history()
    print("Sample historical analytics seeded.")
