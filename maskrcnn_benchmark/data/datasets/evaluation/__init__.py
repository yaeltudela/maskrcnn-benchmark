from maskrcnn_benchmark.data import datasets
import os
from .coco import coco_evaluation
from .voc import voc_evaluation
from .giana_challenge import giana_eval

import logging

def evaluate(dataset, predictions, output_folder, **kwargs):
    """evaluate dataset using different methods based on dataset type.
    Args:
        dataset: Dataset object
        predictions(list[BoxList]): each item in the list represents the
            prediction results for one image.
        output_folder: output folder, to save evaluation files or results.
        **kwargs: other args.
    Returns:
        evaluation result
    """
    args = dict(
        dataset=dataset, predictions=predictions, output_folder=output_folder, **kwargs
    )

    if isinstance(dataset, datasets.COCODataset):
        return coco_evaluation(**args)
    elif isinstance(dataset, datasets.PascalVOCDataset):
        return voc_evaluation(**args)
    elif isinstance(dataset, datasets.CVCClinicDataset):
        coco_eval = coco_evaluation(**args)
        if dataset.name != "cvc-clinic-test":
            return coco_eval
        else:
            giana_eval(**args)
            return coco_eval
    elif isinstance(dataset, datasets.ETISLaribDataset):
        return coco_evaluation(**args)


    else:
        dataset_name = dataset.__class__.__name__
        raise NotImplementedError("Unsupported dataset type {}.".format(dataset_name))
