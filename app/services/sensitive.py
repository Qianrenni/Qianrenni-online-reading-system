import re
import logging


# 读取敏感词文件并加载到内存
def load_sensitive_words(file_path):
    sensitive_words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sensitive_words = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        logging.error(f"Error loading sensitive words from file: {str(e)}")
    return sensitive_words

# 替换敏感词为星号
def replace_sensitive_words(content, sensitive_words):
    for word in sensitive_words:
        # 使用正则替换敏感词，保持敏感词的大小写
        content = re.sub(rf'(?i)\b{re.escape(word)}\b', '*' * len(word), content)
    print('清理敏感词')
    return content
