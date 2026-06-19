let wsURI = "ws://127.0.0.1:8080"
wsURI = "wss://EveryoneCanvasAPI.sabrina.hackclub.app"
const websocket = new WebSocket(wsURI)

let uuid = null
let userStrokes = {}

function sendWebsocketMessage(data){ websocket.send(data) }

function handleWebsocketMessage(data){
    try{ data = JSON.parse(data) }
    catch(e){
        console.error("Data received is not JSON!")
        console.error(data)
    }

    console.log(data)
    let purpose = data["purpose"]
    switch(purpose){
        case "SetUUID":
            uuid = data["uuid"]
            break;
        case "UserStrokes":
            uuid = data["uuid"]
            strokesJson = data["strokes"]

            userStrokes[uuid] = []
            for(let i=0; i<strokesJson.length; i++){
                userStrokes[uuid].push( strokeFromJson(strokesJson[i]) )
            }
            break;
    }
}

websocket.addEventListener("open", ()=>{ console.log("Connected to server!") })

websocket.addEventListener("close", ()=>{ console.log("Disconnected from server!") })

websocket.addEventListener("message", (e)=>{ handleWebsocketMessage(e.data) })

websocket.addEventListener("error", (e)=>{
    console.error("Error connecting to websocket server!")
    console.error(e)
})