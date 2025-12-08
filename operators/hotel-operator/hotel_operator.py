#!/usr/bin/env python3
"""
Lightweight Hotel Operator
Watches Hotel CRDs and creates supporting resources
"""

import os
import time
import logging
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hotel-operator')

# Load kubernetes config
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster config")
except:
    config.load_kube_config()
    logger.info("Loaded kube config from file")

# Initialize API clients
v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()
apps_v1 = client.AppsV1Api()

HOTEL_GROUP = "platform.devops.io"
HOTEL_VERSION = "v1alpha1"
HOTEL_PLURAL = "hotels"
ROOM_PLURAL = "rooms"

# Get environment from env var (prod, staging, test)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'prod')
logger.info(f"Operator running in environment: {ENVIRONMENT}")


def create_namespace(hotel_id, location):
    """Create namespace for hotel"""
    # Namespace format: hotel-{id}-{env} (e.g., hotel-dublin-prod)
    namespace_name = f"{hotel_id}-{ENVIRONMENT}"
    
    namespace = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=namespace_name,
            labels={
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/location": location,
                "platform.devops.io/environment": ENVIRONMENT,
                "platform.devops.io/managed-by": "hotel-operator",
                "argocd.argoproj.io/instance": hotel_id,
            }
        )
    )
    
    try:
        v1.create_namespace(namespace)
        logger.info(f"Created namespace: {namespace_name}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Namespace {namespace_name} already exists")
            # Update labels
            v1.patch_namespace(namespace_name, namespace)
        else:
            logger.error(f"Error creating namespace: {e}")
            raise
    
    return namespace_name


def create_hotel_config_map(hotel_id, namespace, spec):
    """Create ConfigMap with hotel configuration for ApplicationSet"""
    
    # Extract configuration from spec
    # Use environment-specific central namespace for kafka broker
    central_namespace = f"central-{ENVIRONMENT}"
    kafka_broker = spec.get('kafka', {}).get('bootstrapServers', 
                                             f'kafka.{central_namespace}.svc.cluster.local:9092')
    replicas = spec.get('replicas', 1)
    location = spec.get('location', 'unknown')
    
    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=f"{hotel_id}-config",
            namespace="argocd",  # ConfigMap in argocd namespace for ApplicationSet
            labels={
                "platform.devops.io/resource-type": "hotel-instance",
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        data={
            "hotelId": hotel_id,
            "namespace": namespace,
            "location": location,
            "kafkaBroker": kafka_broker,
            "mqttBroker": f"mosquitto.{namespace}.svc.cluster.local",
            "replicas": str(replicas),
        }
    )
    
    try:
        v1.create_namespaced_config_map("argocd", config_map)
        logger.info(f"Created ConfigMap for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"ConfigMap for {hotel_id} already exists, updating...")
            v1.patch_namespaced_config_map(f"{hotel_id}-config", "argocd", config_map)
        else:
            logger.error(f"Error creating ConfigMap: {e}")
            raise


def create_mqtt_secret(hotel_id, namespace):
    """Create MQTT credentials secret"""
    import base64
    
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name="mosquitto-credentials",
            namespace=namespace,
            labels={
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        type="Opaque",
        data={
            # Base64 encoded credentials
            "username": base64.b64encode(b"hotel-user").decode('utf-8'),
            "password": base64.b64encode(f"{hotel_id}-password".encode()).decode('utf-8'),
        }
    )
    
    try:
        v1.create_namespaced_secret(namespace, secret)
        logger.info(f"Created MQTT secret for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Secret already exists for {hotel_id}")
        else:
            logger.error(f"Error creating secret: {e}")


def create_mqtt_broker(hotel_id, namespace, spec):
    """Create MQTT broker (mosquitto) deployment and service"""
    mqtt_config = spec.get('mqtt', {})
    
    if not mqtt_config.get('enabled', True):
        logger.info(f"MQTT disabled for hotel: {hotel_id}")
        return
    
    replicas = mqtt_config.get('replicas', 1)
    port = mqtt_config.get('port', 1883)
    
    # Create ConfigMap for mosquitto
    mosquitto_conf = """
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
"""
    
    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name="mosquitto-config",
            namespace=namespace,
            labels={
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        data={"mosquitto.conf": mosquitto_conf}
    )
    
    try:
        v1.create_namespaced_config_map(namespace, config_map)
        logger.info(f"Created mosquitto ConfigMap for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Mosquitto ConfigMap already exists for {hotel_id}")
        else:
            logger.error(f"Error creating mosquitto ConfigMap: {e}")
    
    # Create PVC for mosquitto data
    pvc = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(
            name="mosquitto-data",
            namespace=namespace,
            labels={
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(
                requests={"storage": "1Gi"}
            )
        )
    )
    
    try:
        v1.create_namespaced_persistent_volume_claim(namespace, pvc)
        logger.info(f"Created PVC for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"PVC already exists for {hotel_id}")
        else:
            logger.error(f"Error creating PVC: {e}")
    
    # Create Deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name="mosquitto",
            namespace=namespace,
            labels={
                "app": "mosquitto",
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(
                match_labels={"app": "mosquitto"}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": "mosquitto"}
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="mosquitto",
                            image="eclipse-mosquitto:latest",
                            ports=[client.V1ContainerPort(container_port=port)],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="mosquitto-config",
                                    mount_path="/mosquitto/config"
                                ),
                                client.V1VolumeMount(
                                    name="mosquitto-data",
                                    mount_path="/mosquitto/data"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        client.V1Volume(
                            name="mosquitto-config",
                            config_map=client.V1ConfigMapVolumeSource(
                                name="mosquitto-config",
                                items=[client.V1KeyToPath(key="mosquitto.conf", path="mosquitto.conf")]
                            )
                        ),
                        client.V1Volume(
                            name="mosquitto-data",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="mosquitto-data"
                            )
                        )
                    ]
                )
            )
        )
    )
    
    try:
        apps_v1.create_namespaced_deployment(namespace, deployment)
        logger.info(f"Created mosquitto deployment for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Mosquitto deployment already exists for {hotel_id}")
        else:
            logger.error(f"Error creating mosquitto deployment: {e}")
    
    # Create Service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name="mosquitto",
            namespace=namespace,
            labels={
                "app": "mosquitto",
                "platform.devops.io/hotel-id": hotel_id,
                "platform.devops.io/managed-by": "hotel-operator",
            }
        ),
        spec=client.V1ServiceSpec(
            selector={"app": "mosquitto"},
            ports=[
                client.V1ServicePort(
                    port=port,
                    target_port=port,
                    name="mqtt"
                )
            ],
            type="ClusterIP"
        )
    )
    
    try:
        v1.create_namespaced_service(namespace, service)
        logger.info(f"Created mosquitto service for hotel: {hotel_id}")
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Mosquitto service already exists for {hotel_id}")
        else:
            logger.error(f"Error creating mosquitto service: {e}")


def create_room_crds(hotel_id, namespace, rooms):
    """Create Room CRDs for each room in the hotel spec"""
    if not rooms:
        logger.info(f"No rooms specified for hotel: {hotel_id}")
        return
    
    for room in rooms:
        room_id = room.get('roomId')
        if not room_id:
            logger.warning(f"Room missing roomId in hotel {hotel_id}")
            continue
        
        room_crd = {
            "apiVersion": f"{HOTEL_GROUP}/{HOTEL_VERSION}",
            "kind": "Room",
            "metadata": {
                "name": f"{hotel_id}-{room_id}",
                "namespace": namespace,
                "labels": {
                    "platform.devops.io/hotel-id": hotel_id,
                    "platform.devops.io/room-id": room_id,
                    "platform.devops.io/managed-by": "hotel-operator",
                }
            },
            "spec": {
                "roomId": room_id,
                "hotelId": hotel_id,
                "replicas": room.get('replicas', 1),
                "sensors": room.get('sensors', {})
            }
        }
        
        try:
            custom_api.create_namespaced_custom_object(
                group=HOTEL_GROUP,
                version=HOTEL_VERSION,
                namespace=namespace,
                plural=ROOM_PLURAL,
                body=room_crd
            )
            logger.info(f"Created Room CRD: {room_id} in hotel {hotel_id}")
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Room {room_id} already exists in {hotel_id}")
            else:
                logger.error(f"Error creating Room CRD: {e}")


def handle_hotel_event(event_type, hotel):
    """Handle hotel CRD events"""
    try:
        metadata = hotel.get('metadata', {})
        spec = hotel.get('spec', {})
        
        hotel_id = spec.get('hotelId')
        location = spec.get('location', 'unknown')
        
        logger.info(f"Processing {event_type} event for hotel: {hotel_id} in {ENVIRONMENT}")
        
        if event_type in ['ADDED', 'MODIFIED']:
            # Create or update resources with environment-specific namespace
            namespace = create_namespace(hotel_id, location)
            create_hotel_config_map(hotel_id, namespace, spec)
            create_mqtt_secret(hotel_id, namespace)
            create_mqtt_broker(hotel_id, namespace, spec)
            
            # Optionally create Room CRDs if specified
            rooms = spec.get('rooms', [])
            if rooms:
                create_room_crds(hotel_id, namespace, rooms)
            
            logger.info(f"Successfully processed hotel: {hotel_id} in namespace: {namespace}")
        
        elif event_type == 'DELETED':
            # Clean up ConfigMap (namespace deletion handled by Kubernetes)
            try:
                v1.delete_namespaced_config_map(
                    f"{hotel_id}-config",
                    "argocd"
                )
                logger.info(f"Deleted ConfigMap for hotel: {hotel_id}")
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Error deleting ConfigMap: {e}")
    
    except Exception as e:
        logger.error(f"Error handling hotel event: {e}", exc_info=True)


def watch_hotels():
    """Watch for Hotel CRD changes"""
    logger.info("Starting hotel operator - watching for Hotel CRDs...")
    
    w = watch.Watch()
    
    while True:
        try:
            for event in w.stream(
                custom_api.list_cluster_custom_object,
                group=HOTEL_GROUP,
                version=HOTEL_VERSION,
                plural=HOTEL_PLURAL,
                timeout_seconds=60
            ):
                event_type = event['type']
                hotel = event['object']
                handle_hotel_event(event_type, hotel)
        
        except ApiException as e:
            logger.error(f"API Exception in watch loop: {e}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error in watch loop: {e}", exc_info=True)
            time.sleep(5)


def main():
    """Main operator loop"""
    logger.info("Hotel Operator Starting...")
    
    # Ensure argocd namespace exists (for ConfigMaps)
    try:
        v1.read_namespace("argocd")
    except ApiException:
        logger.warning("argocd namespace not found - ConfigMaps will fail")
    
    # Start watching
    watch_hotels()


if __name__ == "__main__":
    main()
