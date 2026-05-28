from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user

# Setup SocketIO instance with standard fallbacks
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading', manage_session=False)

# In-memory session visitor counters
# Tracks session ids per form: { form_id: set(request.sid) }
active_form_viewers = {}

def notify_user_socket(user_id, data):
    """Broadcasts a live notification block to a specific user's private socket room."""
    socketio.emit('new_notification', data, room=str(user_id))

def broadcast_live_comment(form_id, comment_data):
    """Sends newly published comment entries immediately to active comment lists."""
    socketio.emit('new_comment', comment_data, room=f"comments_{form_id}")

def broadcast_live_stat(form_id, stat_data):
    """Updates response counters and submission tallies in real-time."""
    socketio.emit('stat_update', stat_data, room=f"stats_{form_id}")

@socketio.on('connect')
def on_connect():
    """Initializes user connection and assigns private notification rooms."""
    if current_user.is_authenticated:
        join_room(str(current_user.id))
        print(f"[Socket] Authenticated User {current_user.name} ({current_user.id}) joined personal room.")
    else:
        print(f"[Socket] Anonymous connection established: sid={request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    """Handles disconnection and cleans up all active form visitor sets."""
    sid = request.sid
    empty_forms = []
    
    for form_id, sids in active_form_viewers.items():
        if sid in sids:
            sids.discard(sid)
            # Broadcast decremented count
            socketio.emit('visitor_count', {'count': len(sids)}, room=f"viewers_{form_id}")
            if not sids:
                empty_forms.append(form_id)
                
    for form_id in empty_forms:
        active_form_viewers.pop(form_id, None)

@socketio.on('join_form_view')
def on_join_form_view(data):
    """Adds a viewer to the form's real-time count room and updates room size."""
    form_id = data.get('form_id')
    if not form_id:
        return
        
    sid = request.sid
    room_name = f"viewers_{form_id}"
    join_room(room_name)
    
    if form_id not in active_form_viewers:
        active_form_viewers[form_id] = set()
        
    active_form_viewers[form_id].add(sid)
    
    # Broadcast count update
    emit('visitor_count', {'count': len(active_form_viewers[form_id])}, room=room_name)

@socketio.on('leave_form_view')
def on_leave_form_view(data):
    """Removes a viewer from the form's count room and broadcasts update."""
    form_id = data.get('form_id')
    if not form_id:
        return
        
    sid = request.sid
    room_name = f"viewers_{form_id}"
    leave_room(room_name)
    
    if form_id in active_form_viewers:
        active_form_viewers[form_id].discard(sid)
        emit('visitor_count', {'count': len(active_form_viewers[form_id])}, room=room_name)

@socketio.on('join_comments_room')
def on_join_comments(data):
    """Subscribes the client to real-time commentary streams on a form."""
    form_id = data.get('form_id')
    if form_id:
        join_room(f"comments_{form_id}")

@socketio.on('join_stats_room')
def on_join_stats(data):
    """Subscribes the client to live response and engagement analytical counters."""
    form_id = data.get('form_id')
    if form_id:
        join_room(f"stats_{form_id}")

# ── NEW: Project & Discover realtime helpers ──────────────────────────────

def broadcast_project_upvote(project_id, new_count):
    """Pushes updated upvote count to everyone viewing a project page."""
    socketio.emit('project_upvote', {'project_id': str(project_id), 'count': new_count},
                  room=f"project_{project_id}")

def broadcast_discover_item(item_data):
    """Pushes new content card to all users on the discover feed."""
    socketio.emit('new_discover_item', item_data, room='discover_feed')

@socketio.on('join_project_room')
def on_join_project(data):
    """Subscribe to live upvote/comment counts for a project page."""
    project_id = data.get('project_id')
    if project_id:
        join_room(f"project_{project_id}")

@socketio.on('join_discover_feed')
def on_join_discover():
    """Subscribe to live new-content events on the discover feed."""
    join_room('discover_feed')

