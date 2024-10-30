from collections import defaultdict, deque

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data.dataloader import DataLoader
from torch.utils.data import random_split
from typing import Iterator

from . import BlockDto, EdgeDto
from src.block.enums import BlockType

MAX_LOSS = 10e8

class Logger:
    """학습 과정을 저장하기 위한 클래스
    """

    def __init__(self):
        pass

class Trainer:
    """모델의 학습을 책임지는 클래스
    """
    def __init__(self, model: nn.Module, train_loader: DataLoader, validate_loader: DataLoader, criterion: nn.Module, optimizer: optim.Optimizer, logger: Logger, checkpoint_interval: int = 10, device: str = 'cpu'):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.validate_loader = validate_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.checkpoint_interval = checkpoint_interval
        self.device = device

    def train_epoch(self):
        self.model.train()  # 모델을 훈련 모드로 전환
        running_loss = 0.0

        for inputs, targets in self.train_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Gradients 초기화
            self.optimizer.zero_grad()

            # Forward pass
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)

            # Backward pass and optimize
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item()

        epoch_loss = running_loss / len(self.train_loader)
        return epoch_loss

    def validate(self):
        self.model.eval()  # 모델을 평가 모드로 전환
        running_loss = 0.0

        with torch.no_grad():  # 평가 시에는 gradients가 필요 없으므로
            for inputs, targets in self.validate_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                running_loss += loss.item()

        epoch_loss = running_loss / len(self.validate_loader)
        return epoch_loss

    def train(self, epochs):
        best_train_loss = MAX_LOSS
        best_valid_loss = MAX_LOSS
        
        for epoch in range(epochs):

            # Training and validation
            train_loss = self.train_epoch()
            valid_loss = self.validate()

            # Logging
            #TODO: Logging 구현

            # Checkpoint (간단히 마지막 모델만 저장)
            if epoch % self.checkpoint_interval == 0:
                torch.save(self.model.state_dict(), f"model_checkpoint_epoch_{epoch+1}.pth")
                
            if best_train_loss > train_loss:
                torch.save(self.model.state_dict(), f"model_checkpoint_best_train_loss.pth")
            
            if best_valid_loss > valid_loss:
                torch.save(self.model.state_dict(), f"model_checkpoint_best_valid_loss.pth")

def validate_data_path(data_path: str) -> bool:
    pass

def create_data_loaders(data_path: str, batch_size: int) -> tuple[DataLoader, DataLoader, DataLoader]:
    pass

def topological_sort(blocks: tuple[BlockDto], edges: tuple[EdgeDto]) -> tuple[BlockDto]:
    graph = defaultdict(list)
    in_degree = {block.id: 0 for block in blocks}

    for edge in edges:
        graph[edge.source_id].append(edge.target_id)
        in_degree[edge.target_id] += 1

    queue = deque([block for block in blocks if in_degree[block.id] == 0])
    sorted_blocks = []

    while queue:
        block = queue.popleft()
        sorted_blocks.append(block)

        for neighbor in graph[block.id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(next(b for b in blocks if b.id == neighbor))

    if len(sorted_blocks) != len(blocks):
        raise ValueError("Cycle detected in the graph; topological sort not possible.")

    return tuple(sorted_blocks)

class UserModel(nn.Module):
    def __init__(self):
        super(UserModel, self).__init__()
        self.layers = nn.Sequential()

    def forward(self, x):
        return self.forward(x)

def convert_block_graph_to_model(blocks: tuple[BlockDto], edges: tuple[EdgeDto]) -> nn.Module:
    sorted_blocks = topological_sort(blocks, edges)

    model = UserModel()

    for block in sorted_blocks:
        if block.type == BlockType.LAYER:
            module = convert_layer_block_to_module(block)
        elif block.type == BlockType.OPERATION:
            module = convert_operation_to_module(block)
        model.layers.add_module(str(len(model.layers)), module)

    return model

# 블록을 nn.Module로 변환하는 함수
def convert_layer_block_to_module(block):
    layer_class = LAYER_MAP.get(block["type"])
    if not layer_class:
        raise ValueError(f"Unsupported layer type: {block['type']}")
    return layer_class(**block["args"])  # 블록 파라미터로 인스턴스 생성

# 손실 기준을 nn.Module로 변환하는 함수
def convert_criterion_block_to_module(block):
    criterion_class = CRITERION_MAP.get(block["type"])
    if not criterion_class:
        raise ValueError(f"Unsupported criterion type: {block['type']}")
    return criterion_class()

def convert_optimizer_to_optimizer(block: BlockDto, parameters: Iterator[nn.Parameter]) -> optim.Optimizer:
    pass