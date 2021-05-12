import os
import numpy as np
import cv2
from scipy.io import loadmat
from utils.construct_triangles import remove_small_area, filter_tri, padding_tri



def realign(img, crop_param, raw_w, raw_h, interpolation, crop_h=256, crop_w=256):
    scale = crop_param[0]
    left, up = int(crop_param[1]), int(crop_param[2])
    canvas = np.zeros([4 * 256, 6 * 256, 3]) if len(img.shape) == 3 else np.zeros([4 * 256, 6 * 256])
    img_stw = 0 if left > 0 else -left
    img_sth = 0 if up > 0 else -up
    canvas_stw = 0 if left < 0 else left
    canvas_sth = 0 if up < 0 else up
    canvas[canvas_sth: canvas_sth + crop_h - img_sth, 
            canvas_stw: canvas_stw + crop_w - img_stw] = img[img_sth:, img_stw:]
    
    w = np.round(canvas.shape[1] * scale).astype(np.int32)
    h = np.round(canvas.shape[0] * scale).astype(np.int32)
    canvas = cv2.resize(
        canvas.astype(np.uint8), (w, h), interpolation=interpolation).astype(np.float32)
    raw_img = canvas[:raw_h, :raw_w]
    return raw_img


def create_bumpmap_inputs(raw_path, crop_path, mask_path, save_path):
    imgs_path = [i for i in os.listdir(raw_path) 
        if i.endswith('png') or i.endswith('jpg') or i.endswith('jpeg')]
    for i, name in enumerate(imgs_path):
        print(i, name)
        raw_image = cv2.imread(os.path.join(raw_path, name))
        rendered_mask = loadmat(os.path.join(mask_path, name.split('.')[0] + '.mat'))['mask'].reshape([256, 256])
        cropped_image = cv2.imread(os.path.join(crop_path, 'vis' ,name.split('.')[0] + '.png'))
        crop_param = loadmat(os.path.join(crop_path, name.split('.')[0] + '.mat'))['crop_param'].reshape([5])
        restored_img = realign(cropped_image, crop_param, raw_image.shape[1], raw_image.shape[0], interpolation=cv2.INTER_LANCZOS4)
        restored_mask = realign(rendered_mask, crop_param, raw_image.shape[1], raw_image.shape[0], interpolation=cv2.INTER_NEAREST)
        restored_mask = np.expand_dims(restored_mask, 2)
        color_mask = np.zeros_like(restored_img)
        color_mask[:, :, -1] = 256
        result = raw_image * ( 1 - restored_mask) + raw_image * restored_mask * 0.8 + color_mask * restored_mask * 0.2
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '.png'), result.astype(np.uint8))
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_raw.png'), raw_image.astype(np.uint8))
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_cropped.png'), cropped_image.astype(np.uint8))
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_restored.png'), restored_img.astype(np.uint8))
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_restored_mask.png'), restored_mask.astype(np.uint8))
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_rendered_mask.png'), rendered_mask.astype(np.uint8))

        bumpmap_mask = restored_mask.copy()
        bumpmap_mask = 1 - bumpmap_mask
        bumpmap_mask = remove_small_area(bumpmap_mask)
        bumpmap_mask = 1 - bumpmap_mask
        bumpmap_input_image_path = os.path.join(save_path, name.split('.')[0] + '_bump_input.png')
        cv2.imwrite(os.path.join(save_path, name.split('.')[0] + '_bump_mask.png'), bumpmap_mask.astype(np.uint8))
        cv2.imwrite(bumpmap_input_image_path, (restored_img * bumpmap_mask).astype(np.uint8))
        imListFile = open(os.path.join(save_path, '..', 'imList.txt'),"w+")
        imListFile.write(bumpmap_input_image_path)
        imListFile.write('\n')
        imListFile.close()



if __name__ == '__main__':
    raw_path = 'examples'
    crop_path = 'output/step1'
    mask_path = 'output/step3'
    save_path = 'output/step4'

    if not os.path.isdir(save_path):
        os.makedirs(save_path)
    create_bumpmap_inputs(raw_path, crop_path, mask_path, save_path)
