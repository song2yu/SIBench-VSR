from vlmeval.dataset import *
from functools import partial


sibench_dataset = {
    'Route_Planning_32frame': partial(SIBench, dataset='Route_Planning', nframe=32, fps=0),
    'Route_Planning_30frame': partial(SIBench, dataset='Route_Planning', nframe=30, fps=0),
    'Route_Planning_16frame': partial(SIBench, dataset='Route_Planning', nframe=16, fps=0),
    'Route_Planning_1fps': partial(SIBench, dataset='Route_Planning', nframe=0, fps=1.0),
}

supported_mixed_datasets_include_video = {}

dataset_groups = [sibench_dataset]

for grp in dataset_groups:
    supported_mixed_datasets_include_video.update(grp)