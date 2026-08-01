# Deep Learning with PyTorch, Second Edition
original repo: https://github.com/deep-learning-with-pytorch/dlwpt-code-2e

## Structure

```
deep-learning-with-pytorch-2e/
├── README.md
├── requirements.txt
│
├── part1_core/
│   ├── ch01_check_installation.ipynb
│   ├── ch02_pretrained_networks.ipynb
│   ├── ch03_tensors.ipynb
│   ├── ch04_real_world_data.ipynb
│   ├── ch05_mechanics_of_learning.ipynb
│   ├── ch06_neural_network_fit.ipynb
│   ├── ch07_birds_vs_airplanes.ipynb
│   └── ch08_convolutions.ipynb
│
├── part2_advanced/
│   ├── ch09_how_transformers_work.ipynb
│   └── ch10_diffusion_models.ipynb
│
└── part2_luna_project/
    ├── README.md
    ├── data/                      # gitignored
    ├── cache/                     # gitignored
    ├── dsets.py                   # shared dataset code, reused across chapters
    ├── model.py                   # shared model code, reused across chapters
    ├── ch11_fight_cancer.ipynb
    ├── ch12_unified_dataset.ipynb
    ├── ch13_classification_model.ipynb
    ├── ch14_metrics_and_augmentation.ipynb
    ├── ch15_segmentation.ipynb
    ├── ch16_multi_gpu_training.ipynb
    └── ch17_deploying_to_production.ipynb
```