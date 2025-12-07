#!/usr/bin/env python3
"""
Hotel Manager - Flask Web UI for managing Hotel and Room CRDs
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hotel-manager')

# Kubernetes configuration
try:
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config")
except:
    config.load_kube_config()
    logger.info("Loaded local Kubernetes config")

# Initialize API clients
custom_api = client.CustomObjectsApi()
v1 = client.CoreV1Api()

# CRD constants
HOTEL_GROUP = "platform.devops.io"
HOTEL_VERSION = "v1alpha1"
HOTEL_PLURAL = "hotels"
ROOM_PLURAL = "rooms"


def get_all_hotels():
    """Get all Hotel CRDs from the cluster"""
    try:
        hotels = custom_api.list_cluster_custom_object(
            group=HOTEL_GROUP,
            version=HOTEL_VERSION,
            plural=HOTEL_PLURAL
        )
        return hotels.get('items', [])
    except ApiException as e:
        logger.error(f"Error fetching hotels: {e}")
        return []


def get_hotel(name, namespace='default'):
    """Get a specific Hotel CRD"""
    try:
        hotel = custom_api.get_namespaced_custom_object(
            group=HOTEL_GROUP,
            version=HOTEL_VERSION,
            namespace=namespace,
            plural=HOTEL_PLURAL,
            name=name
        )
        return hotel
    except ApiException as e:
        logger.error(f"Error fetching hotel {name}: {e}")
        return None


def get_rooms_for_hotel(hotel_id, namespace):
    """Get all Room CRDs for a specific hotel"""
    try:
        rooms = custom_api.list_namespaced_custom_object(
            group=HOTEL_GROUP,
            version=HOTEL_VERSION,
            namespace=namespace,
            plural=ROOM_PLURAL
        )
        # Filter rooms by hotelId
        hotel_rooms = [
            room for room in rooms.get('items', [])
            if room.get('spec', {}).get('hotelId') == hotel_id
        ]
        return hotel_rooms
    except ApiException as e:
        logger.error(f"Error fetching rooms for hotel {hotel_id}: {e}")
        return []


def get_hotel_namespace_status(hotel_id):
    """Check if hotel namespace exists and get pod status"""
    try:
        namespace = v1.read_namespace(hotel_id)
        pods = v1.list_namespaced_pod(hotel_id)
        
        total_pods = len(pods.items)
        running_pods = sum(1 for pod in pods.items if pod.status.phase == 'Running')
        
        return {
            'exists': True,
            'total_pods': total_pods,
            'running_pods': running_pods,
            'status': 'Running' if running_pods == total_pods else 'Partial'
        }
    except ApiException:
        return {
            'exists': False,
            'total_pods': 0,
            'running_pods': 0,
            'status': 'Not Deployed'
        }


@app.route('/')
def index():
    """Main dashboard"""
    hotels = get_all_hotels()
    
    # Enrich hotel data with status
    for hotel in hotels:
        hotel_id = hotel.get('spec', {}).get('hotelId', 'unknown')
        hotel['status_info'] = get_hotel_namespace_status(hotel_id)
        hotel['room_count'] = len(hotel.get('spec', {}).get('rooms', []))
    
    return render_template('index.html', hotels=hotels)


@app.route('/hotels')
def list_hotels():
    """List all hotels"""
    hotels = get_all_hotels()
    
    # Enrich with status information
    for hotel in hotels:
        hotel_id = hotel.get('spec', {}).get('hotelId', 'unknown')
        hotel['status_info'] = get_hotel_namespace_status(hotel_id)
        hotel['room_count'] = len(hotel.get('spec', {}).get('rooms', []))
    
    return render_template('hotels.html', hotels=hotels)


@app.route('/hotel/<name>')
def view_hotel(name):
    """View hotel details"""
    namespace = request.args.get('namespace', 'default')
    hotel = get_hotel(name, namespace)
    
    if not hotel:
        flash(f'Hotel {name} not found', 'error')
        return redirect(url_for('list_hotels'))
    
    hotel_id = hotel.get('spec', {}).get('hotelId', 'unknown')
    status_info = get_hotel_namespace_status(hotel_id)
    rooms = get_rooms_for_hotel(hotel_id, hotel_id)  # Rooms in hotel namespace
    
    return render_template('hotel_detail.html', 
                         hotel=hotel, 
                         status_info=status_info,
                         rooms=rooms)


@app.route('/hotel/create', methods=['GET', 'POST'])
def create_hotel():
    """Create a new hotel"""
    if request.method == 'POST':
        try:
            # Get form data
            hotel_id = request.form.get('hotel_id')
            location = request.form.get('location')
            replicas = int(request.form.get('replicas', 1))
            namespace = request.form.get('namespace', 'default')
            
            # MQTT settings
            mqtt_enabled = request.form.get('mqtt_enabled') == 'on'
            mqtt_port = int(request.form.get('mqtt_port', 1883))
            
            # Kafka settings
            kafka_enabled = request.form.get('kafka_enabled') == 'on'
            kafka_servers = request.form.get('kafka_servers', 'kafka.central.svc.cluster.local:9092')
            
            # Create Hotel CRD
            hotel_crd = {
                "apiVersion": f"{HOTEL_GROUP}/{HOTEL_VERSION}",
                "kind": "Hotel",
                "metadata": {
                    "name": f"{hotel_id}-instance",
                    "namespace": namespace,
                    "labels": {
                        "platform.devops.io/managed-by": "hotel-manager-ui"
                    }
                },
                "spec": {
                    "hotelId": hotel_id,
                    "location": location,
                    "replicas": replicas,
                    "mqtt": {
                        "enabled": mqtt_enabled,
                        "port": mqtt_port,
                        "websocketPort": 9001
                    },
                    "kafka": {
                        "enabled": kafka_enabled,
                        "bootstrapServers": kafka_servers,
                        "topic": f"{hotel_id}-events"
                    },
                    "rooms": []
                }
            }
            
            # Create the hotel
            custom_api.create_namespaced_custom_object(
                group=HOTEL_GROUP,
                version=HOTEL_VERSION,
                namespace=namespace,
                plural=HOTEL_PLURAL,
                body=hotel_crd
            )
            
            flash(f'Hotel {hotel_id} created successfully!', 'success')
            logger.info(f"Created hotel: {hotel_id}")
            return redirect(url_for('list_hotels'))
            
        except ApiException as e:
            flash(f'Error creating hotel: {e.reason}', 'error')
            logger.error(f"Error creating hotel: {e}")
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            logger.error(f"Unexpected error creating hotel: {e}")
    
    return render_template('hotel_create.html')


@app.route('/hotel/<name>/delete', methods=['POST'])
def delete_hotel(name):
    """Delete a hotel"""
    namespace = request.form.get('namespace', 'default')
    
    try:
        custom_api.delete_namespaced_custom_object(
            group=HOTEL_GROUP,
            version=HOTEL_VERSION,
            namespace=namespace,
            plural=HOTEL_PLURAL,
            name=name
        )
        
        flash(f'Hotel {name} deleted successfully!', 'success')
        logger.info(f"Deleted hotel: {name}")
    except ApiException as e:
        flash(f'Error deleting hotel: {e.reason}', 'error')
        logger.error(f"Error deleting hotel: {e}")
    
    return redirect(url_for('list_hotels'))


@app.route('/hotel/<hotel_name>/room/create', methods=['GET', 'POST'])
def create_room(hotel_name):
    """Create a new room for a hotel"""
    namespace = request.args.get('namespace', 'default')
    hotel = get_hotel(hotel_name, namespace)
    
    if not hotel:
        flash(f'Hotel {hotel_name} not found', 'error')
        return redirect(url_for('list_hotels'))
    
    hotel_id = hotel.get('spec', {}).get('hotelId')
    
    if request.method == 'POST':
        try:
            room_id = request.form.get('room_id')
            replicas = int(request.form.get('replicas', 1))
            
            # Sensor settings
            temp_enabled = request.form.get('temp_enabled') == 'on'
            temp_min = float(request.form.get('temp_min', 18.0))
            temp_max = float(request.form.get('temp_max', 26.0))
            
            humidity_enabled = request.form.get('humidity_enabled') == 'on'
            humidity_min = float(request.form.get('humidity_min', 30.0))
            humidity_max = float(request.form.get('humidity_max', 70.0))
            
            light_enabled = request.form.get('light_enabled') == 'on'
            
            # Create Room CRD
            room_crd = {
                "apiVersion": f"{HOTEL_GROUP}/{HOTEL_VERSION}",
                "kind": "Room",
                "metadata": {
                    "name": f"{hotel_id}-{room_id}",
                    "namespace": hotel_id,  # Rooms go in hotel namespace
                    "labels": {
                        "platform.devops.io/hotel-id": hotel_id,
                        "platform.devops.io/room-id": room_id,
                        "platform.devops.io/managed-by": "hotel-manager-ui"
                    }
                },
                "spec": {
                    "roomId": room_id,
                    "hotelId": hotel_id,
                    "replicas": replicas,
                    "sensors": {
                        "temperature": {
                            "enabled": temp_enabled,
                            "minValue": temp_min,
                            "maxValue": temp_max,
                            "interval": 5
                        },
                        "humidity": {
                            "enabled": humidity_enabled,
                            "minValue": humidity_min,
                            "maxValue": humidity_max,
                            "interval": 5
                        },
                        "light": {
                            "enabled": light_enabled
                        }
                    }
                }
            }
            
            # Create the room
            custom_api.create_namespaced_custom_object(
                group=HOTEL_GROUP,
                version=HOTEL_VERSION,
                namespace=hotel_id,
                plural=ROOM_PLURAL,
                body=room_crd
            )
            
            flash(f'Room {room_id} created in {hotel_id}!', 'success')
            logger.info(f"Created room {room_id} in hotel {hotel_id}")
            return redirect(url_for('view_hotel', name=hotel_name, namespace=namespace))
            
        except ApiException as e:
            flash(f'Error creating room: {e.reason}', 'error')
            logger.error(f"Error creating room: {e}")
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            logger.error(f"Unexpected error creating room: {e}")
    
    return render_template('room_create.html', hotel=hotel)


@app.route('/room/<room_name>/delete', methods=['POST'])
def delete_room(room_name):
    """Delete a room"""
    namespace = request.form.get('namespace')
    hotel_name = request.form.get('hotel_name')
    hotel_namespace = request.form.get('hotel_namespace', 'default')
    
    try:
        custom_api.delete_namespaced_custom_object(
            group=HOTEL_GROUP,
            version=HOTEL_VERSION,
            namespace=namespace,
            plural=ROOM_PLURAL,
            name=room_name
        )
        
        flash(f'Room {room_name} deleted successfully!', 'success')
        logger.info(f"Deleted room: {room_name}")
    except ApiException as e:
        flash(f'Error deleting room: {e.reason}', 'error')
        logger.error(f"Error deleting room: {e}")
    
    return redirect(url_for('view_hotel', name=hotel_name, namespace=hotel_namespace))


@app.route('/api/hotels')
def api_hotels():
    """API endpoint for hotels list"""
    hotels = get_all_hotels()
    return jsonify({
        'count': len(hotels),
        'hotels': [
            {
                'name': h.get('metadata', {}).get('name'),
                'hotelId': h.get('spec', {}).get('hotelId'),
                'location': h.get('spec', {}).get('location'),
                'replicas': h.get('spec', {}).get('replicas'),
                'namespace': h.get('metadata', {}).get('namespace')
            }
            for h in hotels
        ]
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
