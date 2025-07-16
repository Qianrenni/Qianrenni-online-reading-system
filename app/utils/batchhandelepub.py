import os
import random
import re
import uuid

from ebooklib import epub
from bs4 import BeautifulSoup
import ebooklib
from werkzeug.utils import secure_filename
import tkinter as tk
from tkinter import filedialog

from app import db
from app.models.book import Book
from app.models.bookContent import BookContent

# from app import db
# from app.models.book import Book
# from app.models.bookContent import BookContent

UPLOAD_FOLDER = 'uploads/books'  # 替换为你想存储书籍的文件夹路径


# 随机生成价格（50 到 100 之间）
def generate_random_price():
    return round(random.uniform(50.0, 100.0), 2)


# 批量处理文件夹中的所有 .epub 文件
def batch_upload_books(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            try:
                if file.lower().endswith('.epub'):
                    epub_path = os.path.join(root, file)
                    print(f"Processing: {epub_path}")

                    # 提取元数据
                    metadata = extract_epub_metadata(epub_path)
                    if not metadata:
                        print(f"Failed to extract metadata for: {epub_path}")
                        continue

                    # 创建唯一目录存储书籍文件
                    unique_dir = str(uuid.uuid4())
                    book_folder = os.path.join(UPLOAD_FOLDER, unique_dir)
                    os.makedirs(book_folder, exist_ok=True)
                    # print(file)
                    # 保存书籍文件

                    # 检查是否为epub文件并提取封面和总页数

                    catalog = {}
                    book = epub.read_epub(epub_path)
                    total_number = len(list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)))
                    for item in book.toc:
                        catalog[str(item.title).replace('.','_')] = book.get_item_with_href(item.href).content.decode('utf-8')
                    for item in book.get_items():
                        if item.get_type() != ebooklib.ITEM_DOCUMENT and item.get_type() != ebooklib.ITEM_COVER and item.get_type() != ebooklib.ITEM_NAVIGATION:
                            with open(os.path.join(book_folder, re.split(r'[/\\]', item.file_name)[-1]), 'wb') as f:
                                f.write(item.content)
                    cover = next(book.get_items_of_type(ebooklib.ITEM_COVER))
                    cover_path = os.path.join(book_folder, re.split(r'[/\\]', cover.file_name)[-1])
                    if cover and cover_path:
                        cover_path = cover_path.replace('\\', '/')
                        with open(cover_path, 'wb') as f:
                            f.write(cover.content)
                    subjects_str_list = [', '.join(map(str, subject)) if isinstance(subject, tuple) else str(subject)
                                         for
                                         subject in metadata['subjects']]
                    # 随机初始化是否收费、免费章节和价格
                    is_paid = random.choice([True, False])
                    free_pages = random.randint(0, total_number // 10) if is_paid else 0  # 假设最多有 10 个免费章节
                    price = generate_random_price() if is_paid else 0.0
                    book_folder = book_folder.replace('\\', '/')
                    # 创建并保存新的书籍对象
                    new_book = Book(
                        title=metadata['title'],
                        author=','.join(metadata['authors']),
                        description=metadata['description'],
                        category=','.join(subjects_str_list),  # 书籍分类
                        total_number=total_number,  # 书籍总页数
                        store_path=book_folder,
                        cover_image=cover_path,
                        free_pages=free_pages,
                        is_paid=is_paid,
                        price=price,
                    )
                    db.session.add(new_book)
                    db.session.commit()
                    new_book_content = BookContent(book_id=new_book.book_id, chapterContents=catalog)
                    new_book_content.save()

                    print(
                        f'the book info is {metadata} {cover_path}  | Paid: {is_paid} | Free Pages: {free_pages} | Price: {price}')
                else:
                    continue
            except Exception as e:
                print(f"Error processing file {file}: {e}")
                continue


def generate_default_subjects(title, authors):
    """生成默认种类"""
    if not title or not authors:
        return ["未知类型"]
    # 根据标题和作者推测可能的种类
    default_subjects = []
    if "科幻" in (title[0][0] if title else "").lower() or any("科幻" in author.lower() for author in authors):
        default_subjects.append("科幻")
    elif "历史" in (title[0][0] if title else "").lower() or any("历史" in author.lower() for author in authors):
        default_subjects.append("历史")
    elif "小说" in (title[0][0] if title else "").lower() or any("小说" in author.lower() for author in authors):
        default_subjects.append("小说")
    elif "技术" in (title[0][0] if title else "").lower() or any("技术" in author.lower() for author in authors):
        default_subjects.append("技术")
    else:
        default_subjects.append("综合")
    return default_subjects


def extract_epub_metadata(epub_path):
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB file: {e}")
        return None
    # 提取元数据
    title = book.get_metadata('DC', 'title')
    authors = book.get_metadata('DC', 'creator')
    subjects = book.get_metadata('DC', 'subject')
    description = book.get_metadata('DC', 'description')
    intro_text = None
    if not description:
        item = next(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
        if item:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            paragraphs = soup.find_all('p')
            if paragraphs:
                intro_text = ' '.join(p.get_text().strip() for p in paragraphs[:3])  # 取前 3 段
    # 如果没有描述且也没有提取到简介，则生成默认简介
    if not description and not intro_text:
        intro_text = f"{title[0][0] if title else '未知标题'} 是一本由 {'、'.join([author[0] for author in authors]) if authors else '未知作者'} 创作的书籍。"
    # 如果没有种类信息，则生成默认种类
    if not subjects:
        subjects = generate_default_subjects(title, [author[0] for author in authors])
    return {
        'title': title[0][0] if title else "未知标题",
        'authors': [author[0] for author in authors] if authors else ["未知作者"],
        'subjects': subjects,
        'description': description[0][0] if description else intro_text,
        # 'cover_image': cover_image,
    }


def run():
    # 使用 tkinter 选择文件夹
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 让用户选择文件夹
    folder_path = filedialog.askdirectory(title="请选择要处理的文件夹")

    if folder_path:

        batch_upload_books(folder_path)
    else:
        print("未选择文件夹，程序退出。")


if __name__ == "__main__":
    run()
