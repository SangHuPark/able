from src.canvas.schemas import Canvas
from src.response.schemas import ImmutableBaseModel


class TrainRequest(ImmutableBaseModel):
    project_name: str
    epoch: int
    batch_size: int
    canvas: Canvas

class TrainResponse(ImmutableBaseModel):
    pass

class TrainResultRequest(ImmutableBaseModel):
    project_name: str
    train_result_name: str