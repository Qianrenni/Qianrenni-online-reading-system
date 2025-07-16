from mongoengine import fields,Document

class BookContent(Document):
    book_id = fields.IntField(required=True,unique=True)
    chapterContents=fields.DictField()
    meta = {
        "collection": "books",  # 指定集合名称
        "indexes": ["book_id"]  # 添加索引
    }