from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class CubeCreate(BaseModel):
    name: str = Field(default="立方体", min_length=1, max_length=40)
    x: float = Field(ge=-1, le=1)
    z: float = Field(ge=-1, le=1)
    height: float = Field(gt=0, le=8)
    color: Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")] = "#2563eb"


class Cube(CubeCreate):
    id: str


app = FastAPI(title="3D Cube Plane API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cubes: list[Cube] = [
    Cube(id="cube-1", name="中心立方体", x=0, z=0, height=2.2, color="#2563eb"),
    Cube(id="cube-2", name="左前立方体", x=-0.55, z=0.38, height=1.2, color="#16a34a"),
    Cube(id="cube-3", name="右后立方体", x=0.48, z=-0.42, height=3.4, color="#f97316"),
]


@app.get("/api/health")
def health_check():
    return {"ok": True, "service": "fastapi"}


@app.get("/api/cubes", response_model=list[Cube])
def list_cubes():
    return cubes


@app.post("/api/cubes", response_model=Cube, status_code=201)
def create_cube(cube: CubeCreate):
    new_cube = Cube(id=f"cube-{uuid4().hex[:8]}", **cube.model_dump())
    cubes.append(new_cube)
    return new_cube


@app.delete("/api/cubes/{cube_id}", status_code=204)
def delete_cube(cube_id: str):
    cubes[:] = [cube for cube in cubes if cube.id != cube_id]
