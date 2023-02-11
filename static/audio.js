//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");


//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);


function startRecording() {
	console.log("recordButton clicked");

	/*
		Simple constraints object, for more advanced audio features see
		https://addpipe.com/blog/audio-constraints-getusermedia/
	*/
    
    var constraints = { audio: true, video:false }

 	/*
    	Disable the record button until we get a success or fail from getUserMedia() 
	*/

	recordButton.disabled = true;
	stopButton.disabled = false;


	/*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

		/*
			create an audio context after getUserMedia is called
			sampleRate might change after getUserMedia is called, like it does on macOS when recording through AirPods
			the sampleRate defaults to the one set in your OS for your playback device
		*/
		audioContext = new AudioContext();

		/*  assign to gumStream for later use  */
		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input,{numChannels:1})

		//start the recording process
		rec.record()

		console.log("Recording started");

	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
    	recordButton.disabled = false;
    	stopButton.disabled = true;

	});
}



function stopRecording() {
	console.log("stopButton clicked");

	//disable the stop button, enable the record too allow for new recordings
	stopButton.disabled = true;
	recordButton.disabled = false;
	
	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);
}



function handle_response(data) {
    // append the bot repsonse to the div
    $('.card-body').append(`
        <div class="d-flex justify-content-start mb-4">
			<div class="img_cont_msg">
					<img src="/static/bot-icon.jpg" class="rounded-circle user_img_msg">
				</div>
			<div class="msg_cotainer">
						${data.response}
				<span class="msg_time">8:40 AM, Today</span>
				</div>
		</div>
    `)
    
    if (data.status == 'finished') {
        // append a row to the table
        $('.problem-table').append(`
               <tr>
                <th scope="row"> ${data.ID}</th>
                <td> ${data.message}</td>
                <td> ${data.lable}</td>
                <td> ${data.address}</td>
                <td> ${data.district}</td>
                <td> ${data.priority}</td>
                <td> ${data.date}</td>
              </tr>
        `)
    }     
  
    // remove the loading indicator
    $( "#loading" ).remove();
}

function handle_message(url) {
    $('.card-body').append(`
        <div class="d-flex justify-content-end mb-4">
			<div class="msg_cotainer_send">
				 <audio controls="" src=${url}></audio>
				<span class="msg_time_send">8:55 AM, Today</span>
			</div>
			<div class="img_cont_msg">
    			<img src="/static/user-icon.jpg" class="rounded-circle user_img_msg">
			</div>
		</div>
    `)
    
        // loading 
    $('.card-body').append(`
        <div class="d-flex justify-content-start mb-4"  id="loading">
    		<div class="img_cont_msg">
				<img src="/static/bot-icon.jpg" class="rounded-circle user_img_msg">
			</div>
    		<div class="msg_cotainer">
				<b>...</b>
    		<span class="msg_time">8:40 AM, Today</span>
			</div>
    	</div>
    `)
}

function createDownloadLink(blob) {

    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');

    //name of .wav file to use during upload and download (without extendion)
    var filename = new Date().toISOString();

    //add controls to the <audio> element
    au.controls = true;
    au.src = url;

    //save to disk link
    link.href = url;
    link.download = filename+".wav"; //download forces the browser to donwload the file using the  filename
    link.innerHTML = "Save to disk";

    //add the new audio element to li
    li.appendChild(au);

    //add the filename to the li
    li.appendChild(document.createTextNode(filename+".wav "))

    //add the save to disk link to li
    li.appendChild(link);
    
    // add audio to user chat
    handle_message(url);
    
    //upload link
    var upload = document.createElement('a');
    upload.href="#";
    upload.innerHTML = "Upload";
    
    var xhr=new XMLHttpRequest();
    xhr.onload=function(e) {
        if(this.readyState === 4) {
              console.log("Server returned: ",e.target.responseText);
         }
    };
    var fd=new FormData();
    fd.append("audio_data",blob, filename);
    xhr.open("POST","/send_voice", true);
	xhr.responseType = 'json';
	xhr.send(fd);
	// 4. This will be called after the response is received
    xhr.onload=function(e) {
          if (xhr.status != 200) { 
            //alert(` ${xhr.statusText.response}`); // e.g. 404: Not Found
            console.log("Server returned: ",e);

          } else { // show the result
            let data = xhr.response;
            //alert(`Done, got ${xhr.response} bytes`); // response is the server response
            //console.log("Server returned1: ", data);
            handle_response(data);
            }
    };

    //li.appendChild(document.createTextNode (" "))//add a space in between
    //li.appendChild(upload)//add the upload link to li

    //add the li element to the ol
    //recordingsList.appendChild(li);
}


