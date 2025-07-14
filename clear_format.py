def clear_format(text):
    # Xóa mọi ký tự không phải chữ cái và số, đưa về chữ thường, cắt bỏ các khoảng trống dư thừa
    text = re.sub(r'\W+', ' ', text)
    return ' '.join(text.lower().split())
