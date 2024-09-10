import base64
from PIL import Image
import json, yaml, os, argparse
import shutil

# Reference : https://github.com/kadapallaNithin/yolo2labelme/blob/main/yolo2labelme.py
# EX : python yolo2labelme.py --input_dir="./datasets/yolo/yolo2labelme/" --out="./outputs/labelme/yolo2labelme/"

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--input_dir', help='input annotated directory')
parser.add_argument('--out', default=None, required=False, help='output dataset directory')
parser.add_argument('--skip', default=False, required=False)
args = parser.parse_args()

data = args.input_dir
out = args.out
skip = args.skip

if not os.path.exists(out):
    os.makedirs(out)


image_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')

def get_shapes(txt_path, width, height, class_labels):
    shapes = open(txt_path).read().split('\n')
    result = []
    for shape in shapes:
        if not shape:
            continue
        values = shape.split()

        class_id = values[0]
        r_shape = dict()
        r_shape["label"] = class_labels[int(class_id)]

        values = [float(value) for value in values[1:]]
        points = []
        for i in range(len(values)//2):
            points.append([values[2*i]*width, values[2*i+1]*height])
        r_shape['points'] = points

        r_shape.update({ "group_id": None,
            "description": "",
            "shape_type": "polygon",
            "flags": {}
        })
        result.append(r_shape)
    return result

def tobase64(file_path):
    with open(file_path, "rb") as image_file:
        data = base64.b64encode(image_file.read())
        return data.decode()

def img_filename_to_ext(img_filename, ext='txt'):
    for img_ext in image_extensions:
        if img_filename.lower().endswith(img_ext):
            return img_filename[:-len(img_ext)] + ext

def is_image_file(file_path):
    file_path = file_path.lower()
    for ext in image_extensions:
        if file_path.endswith(ext):
            return True
    return False

def yolo2labelme_single(txt_path, img_path, class_labels, out_dir):
    img = Image.open(img_path)
    result = {"version": "5.2.1", "flags": {}}
    result['shapes'] = get_shapes(txt_path, img.width, img.height, class_labels)
    result["imagePath"] = img_path
    result["imageData"] = tobase64(img_path)
    result["imageHeight"] = img.height
    result["imageWidth"] = img.width

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    
    img_filename = os.path.basename(img_path)
    json_path = img_filename_to_ext(img_filename,'.json')
    json_path = os.path.join(out_dir,json_path)
    with open(json_path,'w') as f:
        f.write(json.dumps(result))
    shutil.copyfile(img_path, os.path.join(out_dir, img_filename) )

def yolo2labelme(data, out=None, skip=False):
    yaml_path = os.path.join(data,"dataset.yaml")
    with open(yaml_path, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
        class_labels = data_loaded['names']

    if out is None:
        out = os.path.join(os.path.abspath(data),'..','labelmeDataset')
    # for dir_type in ['test', 'train', 'val']:
    for dir_type in ['train','val']:
        dir_path = os.path.join(data, data_loaded[dir_type])
        dir_path = os.path.abspath(dir_path)
        for filename in os.listdir(dir_path):
            img_file = os.path.join(dir_path,filename)
            if is_image_file(img_file):
                txt_file = img_filename_to_ext(img_file.replace('images','labels'), '.txt')
                if os.path.exists(txt_file):
                    yolo2labelme_single(txt_file, img_file, class_labels, out)
                else:
                    if skip == False:
                        raise FileNotFoundError(f"{txt_file} is expected to exist."
                                                +"Pass skip=True to skip silently.\n"
                                                +"skip='print' to print missed paths.")
                    elif skip == 'print':
                        print(f'Missing {txt_file}')


yolo2labelme(data, out, skip)