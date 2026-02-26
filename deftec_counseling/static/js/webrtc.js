let localStream;
let remoteStream;
let peerConnection;

const configuration = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

async function startCall() {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    document.getElementById('localVideo').srcObject = localStream;

    peerConnection = new RTCPeerConnection(configuration);
    localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

    peerConnection.ontrack = event => {
        if (!remoteStream) {
            remoteStream = new MediaStream();
            document.getElementById('remoteVideo').srcObject = remoteStream;
        }
        remoteStream.addTrack(event.track);
    };

    peerConnection.onicecandidate = event => {
        if (event.candidate) {
            chatSocket.send(JSON.stringify({
                'type': 'ice_candidate',
                'data': event.candidate
            }));
        }
    };

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    chatSocket.send(JSON.stringify({
        'type': 'offer',
        'data': offer
    }));
}

function handleSignaling(data) {
    if (data.type === 'offer') {
        peerConnection.setRemoteDescription(new RTCSessionDescription(data.data));
        peerConnection.createAnswer().then(answer => {
            peerConnection.setLocalDescription(answer);
            chatSocket.send(JSON.stringify({
                'type': 'answer',
                'data': answer
            }));
        });
    } else if (data.type === 'answer') {
        peerConnection.setRemoteDescription(new RTCSessionDescription(data.data));
    } else if (data.type === 'ice_candidate') {
        peerConnection.addIceCandidate(new RTCIceCandidate(data.data));
    }
}

function endCall() {
    peerConnection.close();
    localStream.getTracks().forEach(track => track.stop());
    document.getElementById('localVideo').srcObject = null;
    document.getElementById('remoteVideo').srcObject = null;
}

// Attach to buttons in HTML
document.getElementById('start-call').addEventListener('click', startCall);
document.getElementById('end-call').addEventListener('click', endCall);