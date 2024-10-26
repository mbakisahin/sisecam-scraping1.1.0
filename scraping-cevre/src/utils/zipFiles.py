import zlib
import zipfile
import os
import shutil

def copy_raw_data(source_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for website_folder in os.listdir(source_dir):
        website_path = os.path.join(source_dir, website_folder)
        if os.path.isdir(website_path):
            dest_website_path = os.path.join(dest_dir, website_folder)
            os.makedirs(dest_website_path, exist_ok=True)
            for keyword_folder in os.listdir(website_path):
                keyword_path = os.path.join(website_path, keyword_folder)
                if os.path.isdir(keyword_path):
                    dest_keyword_path = os.path.join(dest_website_path, keyword_folder)
                    os.makedirs(dest_keyword_path, exist_ok=True)

def zip_files_with_same_names(source_dir, dest_dir):
    filenames = dict()
    destination_path_list = list()

    for website_folder in os.listdir(source_dir):
        website_path = os.path.join(source_dir, website_folder)
        if os.path.isdir(website_path):
            for keyword_folder in os.listdir(website_path):
                keyword_path = os.path.join(website_path, keyword_folder)
                if os.path.isdir(keyword_path):
                    dest_keyword_path = os.path.join(dest_dir, website_folder, keyword_folder)
                    os.makedirs(dest_keyword_path, exist_ok=True)

                    text_folder_path = os.path.join(keyword_path, 'text')
                    text_files = os.listdir(text_folder_path)
                    for file in text_files:
                        filenames[os.path.splitext(file)[0]] = list()
                        destination_path_list.append(dest_keyword_path)

                    extensions = ['.txt', '.pdf', '.json', '.json']
                    for index_, extension in enumerate(['text', 'pdf', 'json', 'metadata']):
                        current_extension_directory = os.path.join(keyword_path, extension)

                        for file in filenames.keys():
                            temp_file = file + extensions[index_]
                            try:
                                if temp_file in os.listdir(current_extension_directory) or 'metadata_' + temp_file in os.listdir(current_extension_directory):
                                    if extension == 'metadata':
                                        file_ = 'metadata_' + file
                                        will_append_file_name = file_ + extensions[index_]
                                        path_to_add = os.path.join(current_extension_directory, will_append_file_name)
                                        filenames[file].append(path_to_add)
                                    else:
                                        will_append_file_name = file + extensions[index_]
                                        path_to_add = os.path.join(current_extension_directory, will_append_file_name)
                                        filenames[file].append(path_to_add)
                            except FileNotFoundError:
                                print(f"File not found: {temp_file} in {current_extension_directory}. Skipping.")
                            except Exception as e:
                                print(f"An unexpected error occurred: {str(e)}. Skipping.")

    return filenames, destination_path_list

def compress(file_names, path_to_write, zip_name):
    compression = zipfile.ZIP_DEFLATED

    try:
        zf = zipfile.ZipFile(os.path.join(path_to_write, zip_name), mode="w")
        try:
            for file_name in file_names:
                zf.write(file_name, file_name.split('/')[-1], compress_type=compression)
        except FileNotFoundError:
            print(f"File not found: {file_name}. Skipping.")
        except Exception as e:
            print(f"An error occurred while adding {file_name} to the zip: {str(e)}.")
        finally:
            zf.close()
    except FileNotFoundError:
        print(f"Directory not found: {path_to_write}. Unable to create zip.")
    except Exception as e:
        print(f"An unexpected error occurred while creating the zip file: {str(e)}.")
