import asyncio
from kubernetes import client, config as k8s_config
from kubernetes.client.exceptions import ApiException
from utils.logger import get_logger


class KubernetesClient:
    def __init__(self, namespace: str = "default") -> None:
        self.logger = get_logger(__name__)
        self.namespace = namespace
        k8s_config.load_incluster_config()
        self.core = client.CoreV1Api()

    def _pod_name(self, project_id: str) -> str:
        return f"sandbox-{project_id}"

    def _service_name(self, project_id: str) -> str:
        return f"sandbox-{project_id}"

    def _labels(self, project_id: str) -> dict:
        return {"app": "sandbox", "project-id": project_id}

    def _create_pod_sync(self, project_id: str, image: str) -> None:
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=self._pod_name(project_id),
                labels=self._labels(project_id),
            ),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="sandbox",
                        image=image,
                        ports=[client.V1ContainerPort(container_port=8000)],
                    )
                ],
                restart_policy="Never",
            ),
        )
        self.core.create_namespaced_pod(namespace=self.namespace, body=pod)
        self.logger.info("Pod created for project '%s'", project_id)

    def _create_service_sync(self, project_id: str) -> None:
        service = client.V1Service(
            metadata=client.V1ObjectMeta(name=self._service_name(project_id)),
            spec=client.V1ServiceSpec(
                selector=self._labels(project_id),
                ports=[client.V1ServicePort(port=8000, target_port=8000)],
                type="ClusterIP",
            ),
        )
        self.core.create_namespaced_service(namespace=self.namespace, body=service)
        self.logger.info("Service created for project '%s'", project_id)

    def _delete_pod_sync(self, project_id: str) -> None:
        self.core.delete_namespaced_pod(
            name=self._pod_name(project_id),
            namespace=self.namespace,
        )
        self.logger.info("Pod deleted for project '%s'", project_id)

    def _delete_service_sync(self, project_id: str) -> None:
        self.core.delete_namespaced_service(
            name=self._service_name(project_id),
            namespace=self.namespace,
        )
        self.logger.info("Service deleted for project '%s'", project_id)

    async def create_infra(self, project_id: str, image: str) -> None:
        try:
            await asyncio.to_thread(self._create_pod_sync, project_id, image)
            await asyncio.to_thread(self._create_service_sync, project_id)
        except ApiException as e:
            self.logger.error("Failed to create infra for project '%s': %s", project_id, e)
            raise

    async def delete_infra(self, project_id: str) -> None:
        try:
            await asyncio.to_thread(self._delete_service_sync, project_id)
            await asyncio.to_thread(self._delete_pod_sync, project_id)
        except ApiException as e:
            self.logger.error("Failed to delete infra for project '%s': %s", project_id, e)
            raise
