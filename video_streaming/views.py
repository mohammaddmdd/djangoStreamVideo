from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
import os
import mux_python
from mux_python.rest import ApiException
from dotenv import load_dotenv

from video_streaming.forms import SignUpForm
from video_streaming.models import Profile

# Load environment variables
load_dotenv()

# Configure authentication credentials
configuration = mux_python.Configuration()
configuration.username = os.environ.get('MUX_TOKEN')
configuration.password = os.environ.get('MUX_SECRET')

# Initialize API client
live_api = mux_python.LiveStreamsApi(mux_python.ApiClient(configuration))


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        # Handle login form submission
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Authenticate user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Log the user in
                login(request, user)
                return redirect('create_live_stream')
            else:
                # Authentication failed, return an error message
                return render(request, 'login.html', {'form': form, 'error': 'Invalid username or password'})
    else:
        # Render the login form page
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})
    return render(request, 'login.html', {'form': form, 'error': 'Invalid username or password'})


@login_required
def create_live_stream(request):
    if request.method == 'POST':
        # Create a new live stream
        new_asset_settings = mux_python.CreateAssetRequest(playback_policy=[mux_python.PlaybackPolicy.PUBLIC])
        create_live_stream_request = mux_python.CreateLiveStreamRequest(
            playback_policy=[mux_python.PlaybackPolicy.PUBLIC], new_asset_settings=new_asset_settings)
        try:
            # Send the API request to create the live stream
            create_live_stream_response = live_api.create_live_stream(create_live_stream_request)
            stream_key = create_live_stream_response.data.stream_key
            # Store the stream key in the user's profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.stream_key = stream_key
            profile.save()
            # Build the RTMP endpoint URL
            rtmp_endpoint = f"https://stream.mux.com/{create_live_stream_response.data.playback_ids[0].id}.m3u8"
            return render(request, 'stream_created.html', {'rtmp_endpoint': rtmp_endpoint, 'stream_key': stream_key})
        except ApiException as e:
            # Handle any API errors and return an error message
            return HttpResponse('Error creating live stream: ' + str(e))
    else:
        # Render the form page to create a new live stream
        return render(request, 'create_live_stream.html')


@login_required
def view_streams(request):
    # Get the playback ID from the session, or use the first stream in the list as a fallback
    playback_id = request.session.get('playback_id')
    fallback_id = None
    try:
        live_streams = live_api.list_live_streams()
        if live_streams.data:
            fallback_id = live_streams.data[0].id
    except ApiException as e:
        # Handle any API errors and return an error message
        return HttpResponse('Error fetching live streams: ' + str(e))

    # Use the playback ID if available, or the fallback ID if not
    if playback_id:
        stream_data = [{'id': playback_id, 'playback_url': f"https://stream.mux.com/{playback_id}.m3u8"}]
    elif fallback_id:
        stream_data = [{'id': fallback_id, 'playback_url': f"https://stream.mux.com/{fallback_id}.m3u8"}]
    else:
        # Return an error message if there are no live streams available
        return HttpResponse('No live streams available')

    # Pass the stream data and the first stream ID to the template for rendering
    return render(request, 'view_streams.html',
                  {'stream_data': stream_data, 'first_stream_id': stream_data[0]['id']})
