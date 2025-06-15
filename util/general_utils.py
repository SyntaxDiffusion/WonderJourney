import kornia
import numpy as np
import torch
import os
from matplotlib import cm
from torchvision.io import write_video
import imageio


def tensor2im(input_image, imtype=np.uint8):
    if not isinstance(input_image, np.ndarray):
        if isinstance(input_image, torch.Tensor):  # get the data from a variable
            image_tensor = input_image.data
        else:
            return input_image
        image_numpy = image_tensor[0].clamp(0.0, 1.0).cpu().float().numpy()  # convert it into a numpy array
        image_numpy = np.transpose(image_numpy, (1, 2, 0)) * 255.0  # post-processing: tranpose and scaling
    else:  # if it is a numpy array, do nothing
        image_numpy = input_image
    return image_numpy.astype(imtype)


class LatentStorer:
    def __init__(self):
        self.latent = None

    def __call__(self, i, t, latent):
        self.latent = latent


def sobel_filter(disp, mode="sobel", beta=10.0):
    sobel_grad = kornia.filters.spatial_gradient(disp, mode=mode, normalized=False)
    sobel_mag = torch.sqrt(sobel_grad[:, :, 0, Ellipsis] ** 2 + sobel_grad[:, :, 1, Ellipsis] ** 2)
    alpha = torch.exp(-1.0 * beta * sobel_mag).detach()

    return alpha


def apply_colormap(image, cmap="viridis"):
    colormap = cm.get_cmap(cmap)
    colormap = torch.tensor(colormap.colors).to(image.device)
    image_long = (image * 255).long()
    image_long_min = torch.min(image_long)
    image_long_max = torch.max(image_long)
    assert image_long_min >= 0, f"the min value is {image_long_min}"
    assert image_long_max <= 255, f"the max value is {image_long_max}"
    return colormap[image_long[..., 0]]


def apply_depth_colormap(
    depth,
    near_plane=None,
    far_plane=None,
    cmap="viridis",
):
    near_plane = near_plane or float(torch.min(depth))
    far_plane = far_plane or float(torch.max(depth))

    depth = (depth - near_plane) / (far_plane - near_plane + 1e-10)
    depth = torch.clip(depth, 0, 1)

    colored_image = apply_colormap(depth, cmap=cmap)

    return colored_image


def save_video(video, path, fps=10, save_gif=True):
    video = video.permute(0, 2, 3, 1)
    fps = int(fps)
    
    # Convert to numpy and ensure proper format
    video_np = video.cpu().numpy()
    if video_np.dtype != np.uint8:
        video_np = np.clip(video_np * 255, 0, 255).astype(np.uint8)
    
    print(f"Video shape: {video_np.shape}, dtype: {video_np.dtype}")
    
    # Validate video shape
    if len(video_np.shape) != 4 or video_np.shape[3] != 3:
        print(f"Warning: Unexpected video shape {video_np.shape}, expected (frames, height, width, 3)")
        return
    
    # Skip imageio methods and go directly to ffmpeg (most reliable)
    try:
        print("Using ffmpeg for video creation...")
        frames_dir = str(path).replace('.mp4', '_frames')
        os.makedirs(frames_dir, exist_ok=True)
        
        for i, frame in enumerate(video_np):
            frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
            imageio.imwrite(frame_path, frame)
        
        # Create video with subprocess
        import subprocess
        cmd = [
            'ffmpeg', '-y', '-r', str(fps),
            '-i', os.path.join(frames_dir, 'frame_%04d.png'),
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-crf', '23', str(path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            print(f"Video created with ffmpeg: {path} ({os.path.getsize(path)} bytes)")
            # Clean up frames
            import shutil
            shutil.rmtree(frames_dir)
        else:
            print(f"FFmpeg failed. Frames saved to {frames_dir}")
            print(f"Manual command: ffmpeg -r {fps} -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {path}")
            
    except Exception as e:
        print(f"Video creation failed: {e}")
    
    # Create GIF
    if save_gif:
        try:
            gif_path = str(path).replace('.mp4', '.gif')
            imageio.mimsave(gif_path, video_np, duration=1000/fps, loop=0)
            if os.path.exists(gif_path) and os.path.getsize(gif_path) > 0:
                print(f"GIF saved to {gif_path} ({os.path.getsize(gif_path)} bytes)")
        except Exception as e:
            print(f"GIF creation failed: {e}")
