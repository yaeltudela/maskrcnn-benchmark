# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
import random

import torch
import torchvision
from PIL import ImageFilter
from maskrcnn_benchmark.structures.bounding_box import BoxList
from torchvision.transforms import functional as F


class Compose(object):
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, image, target):
        for t in self.transforms:
            image, target = t(image, target)
        return image, target

    def __repr__(self):
        format_string = self.__class__.__name__ + "("
        for t in self.transforms:
            format_string += "\n"
            format_string += "    {0}".format(t)
        format_string += "\n)"
        return format_string


class Resize(object):
    def __init__(self, min_size, max_size):
        if not isinstance(min_size, (list, tuple)):
            min_size = (min_size,)
        self.min_size = min_size
        self.max_size = max_size

    # modified from torchvision to add support for max size
    def get_size(self, image_size):
        w, h = image_size
        size = random.choice(self.min_size)
        max_size = self.max_size
        if max_size is not None:
            min_original_size = float(min((w, h)))
            max_original_size = float(max((w, h)))
            if max_original_size / min_original_size * size > max_size:
                size = int(round(max_size * min_original_size / max_original_size))

        if (w <= h and w == size) or (h <= w and h == size):
            return (h, w)

        if w < h:
            ow = size
            oh = int(size * h / w)
        else:
            oh = size
            ow = int(size * w / h)

        return (oh, ow)

    def __call__(self, image, target=None):
        size = self.get_size(image.size)
        image = F.resize(image, size)
        if target is None:
            return image
        target = target.resize(image.size)
        return image, target


class RandomHorizontalFlip(object):
    def __init__(self, prob=0.5):
        self.prob = prob

    def __call__(self, image, target):
        if random.random() < self.prob:
            image = F.hflip(image)
            target = target.transpose(0)
        return image, target


class RandomGaussianBlur(object):
    def __init__(self, kernel_size=[], prob=0.5):
        self.prob = prob
        self.kernel_size = kernel_size

    def __call__(self, image, target):
        if random.random() < self.prob:
            kernel_size = random.choice(self.kernel_size)
            image = image.filter(ImageFilter.GaussianBlur(kernel_size))

        return image, target


class RandomRotation(object):
    def __init__(self, degrees, resample=False, expand=False):
        if degrees > 90:
            raise ValueError("deggres must be a value between 0 ans 90")

        self.degrees = degrees
        self.resample = resample
        self.expand = expand
        self.angle = random.uniform(-self.degrees, self.degrees)

    def bbox_rotate(self, target, angle, im_size, resample, expand):
        print(target)
        n_target = []
        img_width, img_height = im_size
        for bbox in target.bbox:
            bbox = bbox.cpu().numpy()
            plt.plot([bbox[0], bbox[0], bbox[2], bbox[2]],
                     [bbox[1], bbox[3], bbox[1], bbox[3]])

            scale = img_width / float(img_height)
            x = torch.tensor([bbox[0], bbox[2], bbox[0], bbox[2]])
            y = torch.tensor([bbox[1], bbox[1], bbox[3], bbox[3]])

            from numpy import deg2rad
            angle = torch.tensor(deg2rad(angle))

            x_t = (torch.cos(angle) * x * scale + torch.sin(angle) * y) / scale
            y_t = (torch.sin(angle) * x * scale + torch.cos(angle) * y)

            n_target.append([x_t.min(), y_t.min(), x_t.max(), y_t.max()])

            plt.plot([n_target[0][0], n_target[0][0], n_target[0][2], n_target[0][2]],
                     [n_target[0][1], n_target[0][3], n_target[0][1], n_target[0][3]])

            plt.show()

            print(n_target)

        return BoxList(n_target, im_size)

    def __call__(self, img, target):
        img = F.rotate(img, self.angle, self.resample, self.expand)

        plt.imshow(img)
        rotated_bbox = self.bbox_rotate(target, self.angle, img.size, self.resample, self.expand)

        print(rotated_bbox)
        return img, rotated_bbox


class RandomVerticalFlip(object):
    def __init__(self, prob=0.5):
        self.prob = prob

    def __call__(self, image, target):
        if random.random() < self.prob:
            image = F.vflip(image)
            target = target.transpose(1)
        return image, target


class ColorJitter(object):
    def __init__(self,
                 brightness=None,
                 contrast=None,
                 saturation=None,
                 hue=None,
                 ):
        self.color_jitter = torchvision.transforms.ColorJitter(
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            hue=hue, )

    def __call__(self, image, target):
        image = self.color_jitter(image)
        return image, target


class ToTensor(object):
    def __call__(self, image, target):
        return F.to_tensor(image), target


class Normalize(object):
    def __init__(self, mean, std, to_bgr255=True):
        self.mean = mean
        self.std = std
        self.to_bgr255 = to_bgr255

    def __call__(self, image, target=None):
        if self.to_bgr255:
            image = image[[2, 1, 0]] * 255
        image = F.normalize(image, mean=self.mean, std=self.std)
        if target is None:
            return image
        return image, target


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from maskrcnn_benchmark.data.datasets import CVCClinicDataset


    def scatter_points(bbox):
        bbox = bbox.cpu().numpy()
        plt.plot([bbox[0], bbox[0], bbox[2], bbox[2]],
                 [bbox[1], bbox[3], bbox[1], bbox[3]])


    ds = CVCClinicDataset("datasets/cvc-colondb-612/annotations/train.json", "datasets/cvc-colondb-612/images/",
                          "colon612", Compose([ColorJitter(brightness=0.25, contrast=0.05,saturation=0.05, hue=(-0.05, 0.1))]))

    print(ds[0])
    for box in ds[0][1].bbox:
        scatter_points(box)
    print(ds[0][1].bbox)
    plt.imshow(ds[0][0])
    plt.show()
