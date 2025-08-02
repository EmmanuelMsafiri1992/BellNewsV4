<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{{ __('Edit News Article') }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    {{-- TinyMCE CDN - REMEMBER TO REPLACE 'your-api-key' with your actual API key! --}}
    <script src="{{ asset('tinymce/tinymce.min.js') }}" referrerpolicy="origin"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f2f5;
        }

        .sidebar {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        }

        .sidebar .nav-link {
            color: rgba(255, 255, 255, 0.8);
            padding: 15px 20px;
            border-radius: 8px;
            margin: 5px 0;
            transition: all 0.3s ease;
        }

        .sidebar .nav-link:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            transform: translateX(5px);
        }

        .sidebar .nav-link.active {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-weight: bold;
        }

        .main-content {
            background-color: #f8f9fa;
            min-height: 100vh;
            padding-bottom: 50px;
            /* Space for content below scroll */
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(108, 117, 125, 0.3);
        }

        .btn-secondary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(108, 117, 125, 0.5);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5253 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
            box_shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.5);
        }

        .btn-success {
            background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46, 213, 115, 0.4);
        }


        .welcome-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }

        .alert {
            border-radius: 10px;
            border: none;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }

        .form-control,
        .form-select {
            border-radius: 10px;
            /* Slightly less rounded than buttons for distinction */
            border: 1px solid #ced4da;
            padding: 10px 15px;
            transition: all 0.3s ease;
        }

        .form-control:focus,
        .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .image-thumbnail-container {
            position: relative;
            display: inline-flex; /* Changed to inline-flex for better alignment of inner elements */
            flex-direction: column; /* Stack image and text vertically */
            align-items: center; /* Center content horizontally */
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            padding-bottom: 5px; /* Space for dimensions text */
        }

        .image-thumbnail {
            width: 100px;
            height: 70px; /* Adjusted to make space for text */
            object-fit: cover;
            display: block;
        }

        .image-dims {
            font-size: 0.7em;
            color: #555;
            margin-top: 5px;
        }

        .delete-image-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: rgba(255, 0, 0, 0.7);
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .delete-image-btn:hover {
            background-color: rgba(255, 0, 0, 1);
        }

        /* Specific error styling for custom validation */
        .is-invalid-tinymce+.tox.tox-tinymce {
            border: 1px solid var(--bs-form-invalid-border-color) !important;
        }

        .text-danger-tinymce {
            font-size: 0.875em;
            color: var(--bs-form-invalid-color);
            margin-top: 0.25rem;
        }

        /* New image preview styles */
        .new-image-preview-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
            border: 1px dashed #ced4da;
            padding: 10px;
            border-radius: 8px;
            min-height: 100px; /* Ensure visibility even with no images */
            align-items: center;
            justify-content: center;
            color: #6c757d;
            font-style: italic;
        }

        .new-image-preview-item {
            position: relative;
            width: 100px;
            height: 100px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .new-image-preview-item img {
            width: 100%;
            height: 70%; /* Give space for text below */
            object-fit: cover;
        }

        .new-image-preview-item .image-dims {
            font-size: 0.7em;
            color: #555;
            margin-top: 5px;
        }

        .new-image-preview-item .remove-image-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: rgba(255, 0, 0, 0.7);
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .new-image-preview-item .remove-image-btn:hover {
            background-color: rgba(255, 0, 0, 1);
        }
    </style>
</head>

<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 p-0">
                {{-- Include the sidebar --}}
                @include('admin.sidebar')
            </div>
            <div class="col-md-10 main-content p-4">
                <div class="welcome-section fade-in">
                    <h1><i class="fas fa-newspaper"></i> Edit News Article</h1>
                </div>

                @if (session('success'))
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        {{ session('success') }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                @endif

                @if ($errors->any())
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <ul>
                            @foreach ($errors->all() as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                @endif

                @if (!$news || !is_object($news))
                    <div class="alert alert-danger">News item not found or invalid.</div>
                @else
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card fade-in">
                                <div class="card-body">
                                    <form id="newsForm" method="POST"
                                        action="{{ route('admin.news.update', $news->id) }}"
                                        enctype="multipart/form-data">
                                        @csrf
                                        @method('PUT')
                                        <div class="mb-3">
                                            <label for="title" class="form-label">Title <span
                                                    class="text-danger">*</span></label>
                                            <textarea name="title" id="title" class="form-control" rows="1">{{ old('title', $news->title ?? '') }}</textarea>
                                            <div class="text-danger-tinymce" id="title-error-tinymce"></div>
                                        </div>

                                        <div class="mb-3">
                                            <label for="existing_images" class="form-label">Current Images</label>
                                            @if ($news->images->count() > 0)
                                                <div class="d-flex flex-wrap mb-3">
                                                    @foreach ($news->images as $image)
                                                        <?php
                                                        $imagePath = $image->url;
                                                        // Robustly remove 'public/' or 'storage/' from the beginning of the path
                                                        $imagePath = Str::replaceFirst('public/', '', $imagePath);
                                                        $imagePath = Str::replaceFirst('storage/', '', $imagePath);

                                                        // Get dimensions from the 'sizes' attribute
                                                        $originalDims = null;
                                                        if (isset($image->sizes['original'])) {
                                                            $originalDims = $image->sizes['original'];
                                                        }
                                                        ?>
                                                        <div class="image-thumbnail-container"
                                                            id="image-container-{{ $image->id }}">
                                                            {{-- Corrected image src: Use Storage::url() with the cleaned path --}}
                                                            <img src="{{ Storage::url($imagePath) }}"
                                                                alt="{{ $image->title }}" class="image-thumbnail">
                                                            @if ($originalDims)
                                                                <span class="image-dims">{{ $originalDims['width'] }}x{{ $originalDims['height'] }}px</span>
                                                            @endif
                                                            <button type="button" class="delete-image-btn"
                                                                data-image-id="{{ $image->id }}"
                                                                data-news-id="{{ $news->id }}">
                                                                &times;
                                                            </button>
                                                            <input type="number"
                                                                name="existing_image_duration[{{ $image->id }}]"
                                                                class="form-control form-control-sm mt-1"
                                                                placeholder="Duration (s)"
                                                                value="{{ old('existing_image_duration.' . $image->id, $image->slide_duration / 1000) }}"
                                                                min="1"
                                                                title="Slide duration in seconds for this image">
                                                        </div>
                                                    @endforeach
                                                </div>
                                            @else
                                                <div class="alert alert-info">No images associated with this news
                                                    article.</div>
                                            @endif
                                            <label for="new_images" class="form-label">Upload New Images (Optional, Multiple allowed, Max 1MB
                                                each)</label>
                                            <input type="file" name="new_images[]" id="new_images"
                                                class="form-control" accept="image/*" multiple>
                                            <div class="text-danger" id="new-images-error"></div>
                                            <div id="new-image-preview-container" class="new-image-preview-container">
                                                No new images selected.
                                            </div>
                                            <div class="mb-3 mt-3">
                                                <label for="new_slide_duration" class="form-label">New Images Slide
                                                    Duration (seconds)</label>
                                                <input type="number" name="new_slide_duration" id="new_slide_duration"
                                                    class="form-control" value="{{ old('new_slide_duration', 5) }}"
                                                    min="1">
                                                <div class="form-text">Default slide duration for newly uploaded
                                                    images.</div>
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <label for="description" class="form-label">Description <span
                                                    class="text-danger">*</span></label>
                                            <textarea name="description" id="description" class="form-control" rows="5">{{ old('description', $news->description ?? '') }}</textarea>
                                            <div class="text-danger-tinymce" id="description-error-tinymce"></div>
                                        </div>
                                        <div class="mb-3">
                                            <label for="category_id" class="form-label">Category <span
                                                    class="text-danger">*</span></label>
                                            <select name="category_id" id="category_id" class="form-select">
                                                <option value="">Select a category</option>
                                                @foreach ($categories as $category)
                                                    <option value="{{ $category->id }}"
                                                        {{ old('category_id', $news->category_id) == $category->id ? 'selected' : '' }}>
                                                        {{ $category->name }}
                                                    </option>
                                                @endforeach
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label for="status" class="form-label">Status <span
                                                    class="text-danger">*</span></label>
                                            <select name="status" id="status" class="form-select" required>
                                                <option value="published"
                                                    {{ old('status', $news->status) == 'published' ? 'selected' : '' }}>
                                                    Published</option>
                                                <option value="draft"
                                                    {{ old('status', $news->status) == 'draft' ? 'selected' : '' }}>
                                                    Draft</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label for="date" class="form-label">Date <span
                                                    class="text-danger">*</span></label>
                                            <input type="date" name="date" id="date" class="form-control"
                                                value="{{ old('date', \Carbon\Carbon::parse($news->date)->format('Y-m-d')) }}">
                                        </div>
                                        <div class="d-flex gap-3">
                                            <button type="submit" class="btn btn-primary">
                                                <i class="fas fa-save me-2"></i> Update Article
                                            </button>
                                            <a href="{{ route('admin.news.index') }}" class="btn btn-secondary">
                                                <i class="fas fa-arrow-left me-2"></i> Cancel
                                            </a>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                @endif
            </div>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Helper function to display alerts
            function showAlert(type, message) {
                const alertContainer = document.querySelector('.main-content'); // Or a dedicated container
                const alertId = 'alert-' + Date.now();
                const alertHtml = `
                    <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                        ${message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                // Insert after the welcome section, before the main card
                const welcomeSection = document.querySelector('.welcome-section');
                if (welcomeSection) {
                    welcomeSection.insertAdjacentHTML('afterend', alertHtml);
                } else {
                    alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
                }


                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    const alertElement = document.getElementById(alertId);
                    if (alertElement) {
                        const bsAlert = new bootstrap.Alert(alertElement);
                        bsAlert.close();
                    }
                }, 5000);
            }


            // Auto-dismiss existing session alerts
            const sessionAlerts = document.querySelectorAll('.alert');
            sessionAlerts.forEach(function(alert) {
                if (!alert.id.startsWith('alert-')) { // Avoid double-handling for dynamically created alerts
                    setTimeout(function() {
                        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                        bsAlert.close();
                    }, 5000);
                }
            });

            // Initialize TinyMCE
            if (typeof tinymce !== 'undefined') {
                tinymce.init({
                    selector: '#description, #title', // Selects both textareas by their IDs
                    plugins: 'advlist autolink lists link image charmap preview anchor pagebreak nonbreaking anchor insertdatetime wordcount fullscreen code fontsize', // Added 'fontsize'
                    toolbar: 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link image | code | fullscreen | help | fontsize', // Added 'fontsize' to toolbar
                    height: 200,
                    menubar: false,
                    content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:16px }',
                    license_key: 'gpl',
                    external_plugins: { // Added external_plugins for fontsize
                        'fontsize': '{{ asset("tinymce/plugins/fontsize/plugin.min.js") }}'
                    },
                    setup: function(editor) {
                        editor.on('change', function() {
                            const textarea = document.getElementById(editor.id);
                            if (textarea) {
                                textarea.classList.remove('is-invalid-tinymce');
                            }
                            const errorElement = document.getElementById(editor.id + '-error-tinymce');
                            if (errorElement) {
                                errorElement.textContent = '';
                            }
                        });
                    }
                });
            } else {
                console.error(
                    "TinyMCE script not loaded or 'tinymce' object is not defined. Please ensure the CDN is accessible."
                );
            }

            // Handle image deletion
            document.querySelectorAll('.delete-image-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const imageId = this.dataset.imageId;
                    const newsId = this.dataset.newsId;
                    if (confirm('Are you sure you want to delete this image?')) {
                        fetch(`/admin/news/${newsId}/images/${imageId}`, {
                                method: 'DELETE',
                                headers: {
                                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')
                                        .content, // Ensure CSRF token is sent
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'X-Requested-With': 'XMLHttpRequest'
                                }
                            })
                            .then(response => {
                                const contentType = response.headers.get("content-type");
                                if (contentType && contentType.indexOf("application/json") !== -1) {
                                    return response.json();
                                } else {
                                    return response.text().then(text => {
                                        throw new Error('Server response was not JSON: ' + text);
                                    });
                                }
                            })
                            .then(data => {
                                if (data.success) {
                                    document.getElementById(`image-container-${imageId}`).remove();
                                    showAlert('success', data.message); // Use custom alert
                                } else {
                                    showAlert('danger', 'Error: ' + data.message); // Use custom alert
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                showAlert('danger', `An error occurred while deleting the image: ${error.message}`);
                            });
                    }
                });
            });

            // --- New Image Preview Logic for Edit Page ---
            const newImagesInput = document.getElementById('new_images');
            const newImagePreviewContainer = document.getElementById('new-image-preview-container');
            const newImagesErrorDiv = document.getElementById('new-images-error');
            let newSelectedFiles = []; // To hold new File objects for submission

            newImagesInput.addEventListener('change', function() {
                newImagePreviewContainer.innerHTML = ''; // Clear previous previews
                newImagesErrorDiv.textContent = ''; // Clear previous image errors
                newSelectedFiles = []; // Reset selected files array

                if (this.files.length === 0) {
                    newImagePreviewContainer.innerHTML = 'No new images selected.';
                    newImagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                    return;
                }

                const dataTransfer = new DataTransfer();
                let hasInvalidFile = false;

                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];

                    // Client-side validation
                    if (!file.type.startsWith('image/')) {
                        newImagesErrorDiv.textContent = 'Only image files are allowed.';
                        hasInvalidFile = true;
                        break;
                    }
                    if (file.size > 1 * 1024 * 1024) { // 1MB limit
                        newImagesErrorDiv.textContent = 'Each new image must be under 1MB.';
                        hasInvalidFile = true;
                        break;
                    }

                    newSelectedFiles.push(file);
                    dataTransfer.items.add(file);

                    const reader = new FileReader();
                    reader.onload = (function(file) {
                        return function(e) {
                            const previewItem = document.createElement('div');
                            previewItem.classList.add('new-image-preview-item');

                            const img = document.createElement('img');
                            img.src = e.target.result;
                            img.alt = file.name;

                            const dimsSpan = document.createElement('span');
                            dimsSpan.classList.add('image-dims');
                            img.onload = function() {
                                dimsSpan.textContent = `${img.naturalWidth}x${img.naturalHeight}px`;
                            };

                            const removeBtn = document.createElement('button');
                            removeBtn.classList.add('remove-image-btn');
                            removeBtn.innerHTML = '&times;';
                            removeBtn.type = 'button';

                            removeBtn.addEventListener('click', function() {
                                previewItem.remove();
                                const index = newSelectedFiles.indexOf(file);
                                if (index > -1) {
                                    newSelectedFiles.splice(index, 1);
                                }
                                updateNewFileInputFiles();
                                if (newSelectedFiles.length === 0) {
                                    newImagePreviewContainer.innerHTML = 'No new images selected.';
                                    newImagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                                }
                            });

                            previewItem.appendChild(img);
                            previewItem.appendChild(dimsSpan);
                            previewItem.appendChild(removeBtn);
                            newImagePreviewContainer.appendChild(previewItem);
                        };
                    })(file);
                    reader.readAsDataURL(file);
                }

                if (hasInvalidFile) {
                    newImagePreviewContainer.innerHTML = 'No new images selected.';
                    newSelectedFiles = [];
                    newImagesInput.value = '';
                    newImagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                } else {
                    this.files = dataTransfer.files;
                    if (newSelectedFiles.length > 0) {
                        newImagePreviewContainer.classList.remove('justify-content-center', 'text-muted', 'font-style-italic');
                    }
                }
            });

            function updateNewFileInputFiles() {
                const dataTransfer = new DataTransfer();
                newSelectedFiles.forEach(file => dataTransfer.items.add(file));
                newImagesInput.files = dataTransfer.files;
            }


            // Handle news form submission with AJAX
            const newsForm = document.getElementById('newsForm');
            if (newsForm) {
                newsForm.addEventListener('submit', function(event) {
                    event.preventDefault();

                    // Manually trigger TinyMCE save to update the textarea content
                    if (typeof tinymce !== 'undefined') {
                        tinymce.triggerSave();
                    }

                    let isValid = true;

                    // Custom validation for TinyMCE fields
                    const titleEditor = tinymce.get('title');
                    const descriptionEditor = tinymce.get('description');
                    const titleTextarea = document.getElementById('title');
                    const descriptionTextarea = document.getElementById('description');
                    const titleErrorDiv = document.getElementById('title-error-tinymce');
                    const descriptionErrorDiv = document.getElementById('description-error-tinymce');

                    // Validate title
                    if (!titleEditor || titleEditor.getContent().trim() === '') {
                        titleTextarea.classList.add('is-invalid-tinymce');
                        titleErrorDiv.textContent = 'The title field is required.';
                        isValid = false;
                    } else {
                        titleTextarea.classList.remove('is-invalid-tinymce');
                        titleErrorDiv.textContent = '';
                    }

                    // Validate description
                    if (!descriptionEditor || descriptionEditor.getContent().trim() === '') {
                        descriptionTextarea.classList.add('is-invalid-tinymce');
                        descriptionErrorDiv.textContent = 'The description field is required.';
                        isValid = false;
                    } else {
                        descriptionTextarea.classList.remove('is-invalid-tinymce');
                        descriptionErrorDiv.textContent = '';
                    }

                    // Validate other standard required fields (category_id, status, date)
                    const categoryId = document.getElementById('category_id');
                    const status = document.getElementById('status');
                    const date = document.getElementById('date');

                    if (!categoryId.value) {
                        categoryId.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        categoryId.classList.remove('is-invalid');
                    }

                    if (!status.value) {
                        status.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        status.classList.remove('is-invalid');
                    }

                    if (!date.value) {
                        date.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        date.classList.remove('is-invalid');
                    }


                    if (!isValid) {
                        showAlert('danger', 'Please correct the highlighted errors.');
                        return;
                    }

                    const formData = new FormData(this);
                    // Manually append new files from our newSelectedFiles array
                    formData.delete('new_images[]'); // Clear existing entries if any
                    newSelectedFiles.forEach(file => {
                        formData.append('new_images[]', file);
                    });

                    const button = this.querySelector('button[type="submit"]');
                    const originalHtml = button.innerHTML;

                    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Updating...';
                    button.disabled = true;

                    fetch(this.action, {
                            method: 'POST', // Laravel uses POST for PUT/PATCH via _method field
                            body: formData,
                            headers: {
                                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
                                'Accept': 'application/json', // Expect JSON response
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        })
                        .then(response => {
                            const contentType = response.headers.get("content-type");
                            if (contentType && contentType.indexOf("application/json") !== -1) {
                                if (!response.ok) {
                                    return response.json().then(err => {
                                        throw err;
                                    });
                                }
                                return response.json();
                            } else {
                                return response.text().then(text => {
                                    throw new Error('Server response was not JSON: ' + text);
                                });
                            }
                        })
                        .then(data => {
                            button.innerHTML = originalHtml;
                            button.disabled = false;

                            if (data && data.success) {
                                showAlert('success', data.message || 'News article updated successfully');
                                if (data.redirect) {
                                    window.location.href = data.redirect;
                                }
                            } else {
                                // This branch might be hit if the backend explicitly sends success: false with a message
                                throw new Error(data?.message || 'Failed to update news article');
                            }
                        })
                        .catch(error => {
                            button.innerHTML = originalHtml;
                            button.disabled = false;
                            let errorMessage = 'Failed to update news article.';
                            if (error.errors) {
                                errorMessage += '<ul>';
                                for (const key in error.errors) {
                                    errorMessage += `<li>${error.errors[key].join(', ')}</li>`;
                                }
                                errorMessage += '</ul>';
                            } else if (error.message) {
                                errorMessage += `: ${error.message}`;
                            }
                            showAlert('danger', errorMessage);
                        });
                });
            }
        }); // End of DOMContentLoaded
    </script>
</body>

</html>
