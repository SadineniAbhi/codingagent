from functools import lru_cache
from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from agent.agent import build_graph
from service.agent_service import AgentService
from service.project_service import ProjectService
from clients.kuberentes import KubernetesClient
from utils.env import settings


@lru_cache
def get_checkpointer() -> MongoDBSaver:
    client = MongoClient(settings.MONGO_DB_URI)
    return MongoDBSaver(client=client, db_name="langgraph")


@lru_cache
def get_agent_service() -> AgentService:
    return AgentService(graph=build_graph(get_checkpointer()))


@lru_cache
def get_kubernetes_client() -> KubernetesClient:
    return KubernetesClient()


@lru_cache
def get_project_service() -> ProjectService:
    return ProjectService(k8s=get_kubernetes_client())
