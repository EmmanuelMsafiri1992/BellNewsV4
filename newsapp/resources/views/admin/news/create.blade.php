<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{{ __('Create News Article') }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Common styles imported from dashboard for consistency */
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
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
        }

        .main-content {
            background-color: #f8f9fa;
            min-height: 100vh;
            padding: 20px;
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
        }

        .form-label {
            font-weight: 600;
            color: #333;
        }

        .form-control,
        .form-select {
            border-radius: 10px;
            padding: 10px 15px;
            border: 1px solid #ced4da;
        }

        .form-control:focus,
        .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.25rem rgba(102, 126, 234, 0.25);
        }

        /* Custom style for modal header to match gradient theme */
        .modal-header-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom: none;
            /* Remove default border */
        }

        /* Ensure close button is visible on dark background */
        .modal-header-gradient .btn-close {
            filter: invert(1) grayscale(100%) brightness(200%);
            /* Makes it white */
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

        /* Image preview styles */
        .image-preview-container {
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

        .image-preview-item {
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

        .image-preview-item img {
            width: 100%;
            height: 70%; /* Give space for text below */
            object-fit: cover;
        }

        .image-preview-item .image-dims {
            font-size: 0.7em;
            color: #555;
            margin-top: 5px;
        }

        .image-preview-item .remove-image-btn {
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

        .image-preview-item .remove-image-btn:hover {
            background-color: rgba(255, 0, 0, 1);
        }
    </style>
</head>

<body>
    <div class="d-flex">
        {{-- Include the sidebar --}}
        @include('admin.sidebar')

        <div class="flex-grow-1">
            {{-- Navbar --}}
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">
                        <i class="fas fa-plus-circle me-2"></i> {{ __('Create News Article') }}
                    </a>
                </div>
            </nav>

            <div class="main-content">
                <div id="alert-container">
                    {{-- Alerts will be injected here --}}
                </div>

                <div class="row justify-content-center">
                    <div class="col-md-10">
                        <div class="card p-4">
                            <div class="card-header bg-transparent mb-4">
                                <h4 class="mb-0">{{ __('Create New News Article') }}</h4>
                            </div>
                            <div class="card-body">
                                <form id="news-form" action="{{ route('admin.news.store') }}" method="POST"
                                    enctype="multipart/form-data">
                                    @csrf

                                    <div class="mb-3">
                                        <label for="title" class="form-label">{{ __('Title') }} <span
                                                class="text-danger">*</span></label>
                                        <textarea class="form-control" id="title" name="title" rows="2">{{ old('title') }}</textarea>
                                        <div class="text-danger-tinymce" id="title-error-tinymce"></div>
                                        @error('title')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="mb-3">
                                        <label for="description" class="form-label">{{ __('Description') }} <span
                                                class="text-danger">*</span></label>
                                        <textarea class="form-control" id="description" name="description" rows="8">{{ old('description') }}</textarea>
                                        <div class="text-danger-tinymce" id="description-error-tinymce"></div>
                                        @error('description')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="mb-3">
                                        <label for="category_id" class="form-label">{{ __('Category') }} <span
                                                class="text-danger">*</span></label>
                                        <div class="input-group">
                                            <select class="form-select" id="category_id" name="category_id" required>
                                                <option value="">{{ __('Select a category') }}</option>
                                                @foreach ($categories as $category)
                                                    <option value="{{ $category->id }}"
                                                        {{ old('category_id') == $category->id ? 'selected' : '' }}>
                                                        {{ $category->name }}
                                                    </option>
                                                @endforeach
                                            </select>
                                            <button class="btn btn-primary" type="button"
                                                id="createCategoryBtn" data-bs-toggle="modal"
                                                data-bs-target="#createCategoryModal">
                                                <i class="fas fa-plus me-1"></i> {{ __('New Category') }}
                                            </button>
                                        </div>
                                        @error('category_id')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="mb-3">
                                        <label for="images" class="form-label">{{ __('Upload Images') }} <span
                                                class="text-danger">* (Multiple allowed, Max 1MB each)</span></label>
                                        <input type="file" class="form-control" id="images" name="images[]" multiple
                                            accept="image/*">
                                        <div class="text-danger" id="images-error"></div>
                                        @error('images.*')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                        <div id="image-preview-container" class="image-preview-container">
                                            No images selected.
                                        </div>
                                    </div>

                                    <div class="mb-3">
                                        <label for="status" class="form-label">{{ __('Status') }} <span
                                                class="text-danger">*</span></label>
                                        <select class="form-select" id="status" name="status" required>
                                            <option value="draft" {{ old('status') == 'draft' ? 'selected' : '' }}>
                                                {{ __('Draft') }}</option>
                                            <option value="published"
                                                {{ old('status') == 'published' ? 'selected' : '' }}>
                                                {{ __('Published') }}</option>
                                        </select>
                                        @error('status')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="mb-3">
                                        <label for="date" class="form-label">{{ __('Publication Date') }} <span
                                                class="text-danger">*</span></label>
                                        <input type="date" class="form-control" id="date" name="date"
                                            value="{{ old('date', date('Y-m-d')) }}" required>
                                        @error('date')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="mb-4">
                                        <label for="slider_duration" class="form-label">{{ __('Slider Duration (seconds)') }}</label>
                                        <input type="number" class="form-control" id="slider_duration" name="slider_duration"
                                            value="{{ old('slider_duration', 5) }}" min="1">
                                        @error('slider_duration')
                                            <div class="text-danger">{{ $message }}</div>
                                        @enderror
                                    </div>

                                    <div class="d-flex justify-content-end">
                                        <a href="{{ route('admin.news.index') }}"
                                            class="btn btn-secondary me-2">{{ __('Cancel') }}</a>
                                        <button type="submit" class="btn btn-primary" id="submit-button">
                                            <span class="spinner-border spinner-border-sm d-none" role="status"
                                                aria-hidden="true"></span>
                                            <i class="fas fa-save me-2"></i> {{ __('Save News Article') }}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    {{-- Create Category Modal --}}
    <div class="modal fade" id="createCategoryModal" tabindex="-1" aria-labelledby="createCategoryModalLabel"
        aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header modal-header-gradient"> {{-- Applied custom gradient class --}}
                    <h5 class="modal-title" id="createCategoryModalLabel">{{ __('Create New Category') }}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"
                        aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="createCategoryForm">
                        <div class="mb-3">
                            <label for="category_name" class="form-label">{{ __('Category Name') }} <span
                                    class="text-danger">*</span></label>
                            <input type="text" class="form-control" id="category_name" name="name" required>
                            <div class="text-danger mt-1" id="category-name-error"></div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary"
                        data-bs-dismiss="modal">{{ __('Close') }}</button>
                    <button type="button" class="btn btn-primary" id="saveCategoryBtn">
                        <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                        <i class="fas fa-plus-circle me-2"></i> {{ __('Save Category') }}
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script src="{{ asset('tinymce/tinymce.min.js') }}"></script>
    <script>
        // Initialize TinyMCE for both description and title textareas
        tinymce.init({
            selector: '#description, #title', // Selects both textareas by their IDs
            plugins: 'advlist autolink lists link image charmap preview anchor pagebreak nonbreaking anchor insertdatetime wordcount fullscreen code',
            toolbar: 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link image | code | fullscreen | help | fontsize',
            height: 200,
            menubar: false,
            content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:16px }',
            license_key: 'gpl', // Essential for TinyMCE to run without evaluation warnings
            external_plugins: {
                'fontsize': '{{ asset("tinymce/plugins/fontsize/plugin.min.js") }}'
            },
            setup: function(editor) {
                editor.on('change', function() {
                    // When content changes, remove validation errors
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


        document.addEventListener('DOMContentLoaded', function() {
            const newsForm = document.getElementById('news-form');
            const submitButton = document.getElementById('submit-button');
            const alertContainer = document.getElementById('alert-container');
            const imagesInput = document.getElementById('images');
            const imagePreviewContainer = document.getElementById('image-preview-container');
            const imagesErrorDiv = document.getElementById('images-error');

            let selectedFiles = []; // To hold File objects for submission

            // --- Image Preview Logic ---
            imagesInput.addEventListener('change', function() {
                imagePreviewContainer.innerHTML = ''; // Clear previous previews
                imagesErrorDiv.textContent = ''; // Clear previous image errors
                selectedFiles = []; // Reset selected files array

                if (this.files.length === 0) {
                    imagePreviewContainer.innerHTML = 'No images selected.';
                    imagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                    return;
                }

                const dataTransfer = new DataTransfer(); // Create a new DataTransfer object

                let hasInvalidFile = false;

                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];

                    // Client-side validation
                    if (!file.type.startsWith('image/')) {
                        imagesErrorDiv.textContent = 'Only image files are allowed.';
                        hasInvalidFile = true;
                        break; // Stop processing if an invalid file type is found
                    }
                    if (file.size > 1 * 1024 * 1024) { // 1MB limit
                        imagesErrorDiv.textContent = 'Each image must be under 1MB.';
                        hasInvalidFile = true;
                        break; // Stop processing if an oversized file is found
                    }

                    selectedFiles.push(file); // Add valid file to our array
                    dataTransfer.items.add(file); // Add file to DataTransfer object

                    const reader = new FileReader();
                    reader.onload = (function(file) { // Use closure to capture file
                        return function(e) {
                            const previewItem = document.createElement('div');
                            previewItem.classList.add('image-preview-item');

                            const img = document.createElement('img');
                            img.src = e.target.result;
                            img.alt = file.name;

                            const dimsSpan = document.createElement('span');
                            dimsSpan.classList.add('image-dims');
                            // Get image dimensions from the loaded image
                            img.onload = function() {
                                dimsSpan.textContent = `${img.naturalWidth}x${img.naturalHeight}px`;
                            };

                            const removeBtn = document.createElement('button');
                            removeBtn.classList.add('remove-image-btn');
                            removeBtn.innerHTML = '&times;';
                            removeBtn.type = 'button'; // Important for forms

                            removeBtn.addEventListener('click', function() {
                                previewItem.remove(); // Remove the preview item from DOM
                                // Remove the file from selectedFiles array
                                const index = selectedFiles.indexOf(file);
                                if (index > -1) {
                                    selectedFiles.splice(index, 1);
                                }
                                // Update the actual file input's files list
                                updateFileInputFiles();
                                if (selectedFiles.length === 0) {
                                    imagePreviewContainer.innerHTML = 'No images selected.';
                                    imagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                                }
                            });

                            previewItem.appendChild(img);
                            previewItem.appendChild(dimsSpan); // Add dimensions below image
                            previewItem.appendChild(removeBtn);
                            imagePreviewContainer.appendChild(previewItem);
                        };
                    })(file); // Pass file to the closure
                    reader.readAsDataURL(file);
                }

                if (hasInvalidFile) {
                    imagePreviewContainer.innerHTML = 'No images selected.';
                    selectedFiles = []; // Clear files if invalid
                    imagesInput.value = ''; // Clear the input
                    imagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                } else {
                    // Update the file input's files with the valid ones
                    this.files = dataTransfer.files;
                    if (selectedFiles.length > 0) {
                        imagePreviewContainer.classList.remove('justify-content-center', 'text-muted', 'font-style-italic');
                    }
                }
            });

            function updateFileInputFiles() {
                const dataTransfer = new DataTransfer();
                selectedFiles.forEach(file => dataTransfer.items.add(file));
                imagesInput.files = dataTransfer.files;
            }


            // --- News Form Submission ---
            if (newsForm && submitButton) {
                newsForm.addEventListener('submit', function(e) {
                    e.preventDefault(); // Prevent default HTML5 form submission

                    // Manually trigger TinyMCE save to update the textarea content
                    tinymce.triggerSave();

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

                    // Validate images (required)
                    if (selectedFiles.length === 0) {
                        imagesInput.classList.add('is-invalid');
                        imagesErrorDiv.textContent = 'At least one image is required.';
                        isValid = false;
                    } else {
                        imagesInput.classList.remove('is-invalid');
                        imagesErrorDiv.textContent = '';
                    }


                    if (!isValid) {
                        // If any validation fails, stop submission
                        showAlert('danger', 'Please fill in all required fields and upload at least one image.');
                        return;
                    }

                    // Show spinner and disable button
                    const originalHtml = submitButton.innerHTML;
                    submitButton.innerHTML =
                        `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>{{ __('Saving...') }}`;
                    submitButton.disabled = true;


                    const formData = new FormData(newsForm);
                    // Manually append files from our selectedFiles array
                    // Clear existing 'images[]' entries first if any from original input
                    formData.delete('images[]');
                    selectedFiles.forEach(file => {
                        formData.append('images[]', file);
                    });


                    fetch(newsForm.action, {
                            method: 'POST',
                            headers: {
                                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')
                                    .content,
                                'Accept': 'application/json'
                            },
                            body: formData
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
                                showAlert('success', data.message);
                                if (data.redirect) {
                                    window.location.href = data.redirect;
                                } else {
                                    newsForm.reset();
                                    // Clear TinyMCE editors
                                    tinymce.get('description').setContent('');
                                    tinymce.get('title').setContent('');
                                    // Clear image previews
                                    imagePreviewContainer.innerHTML = 'No images selected.';
                                    imagePreviewContainer.classList.add('justify-content-center', 'text-muted', 'font-style-italic');
                                    selectedFiles = [];
                                    imagesInput.value = ''; // Clear file input
                                    submitButton.innerHTML = originalHtml;
                                    submitButton.disabled = false;
                                }
                            } else {
                                throw new Error(data?.message || 'Failed to save news article');
                            }
                        })
                        .catch(error => {
                            submitButton.innerHTML = originalHtml;
                            submitButton.disabled = false;
                            showAlert('danger', `Failed to save news article: ${error.message}`);
                        });
                });
            }

            // --- Category Modal Logic ---
            const createCategoryModal = new bootstrap.Modal(document.getElementById('createCategoryModal'));
            const createCategoryForm = document.getElementById('createCategoryForm');
            const saveCategoryBtn = document.getElementById('saveCategoryBtn');
            const categoryNameInput = document.getElementById('category_name');
            const categoryNameError = document.getElementById('category-name-error');
            const categorySelect = document.getElementById('category_id');

            if (saveCategoryBtn && createCategoryForm && categorySelect) {
                saveCategoryBtn.addEventListener('click', function() {
                    const categoryName = categoryNameInput.value.trim();
                    if (!categoryName) {
                        categoryNameError.textContent = 'Category name is required.';
                        categoryNameInput.focus();
                        return;
                    } else {
                        categoryNameError.textContent = '';
                    }

                    // Show spinner and disable button
                    const originalBtnHtml = saveCategoryBtn.innerHTML;
                    saveCategoryBtn.innerHTML =
                        `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>{{ __('Saving...') }}`;
                    saveCategoryBtn.disabled = true;

                    const formData = new FormData();
                    formData.append('name', categoryName);

                    fetch("{{ route('admin.categories.store') }}", {
                            method: 'POST',
                            headers: {
                                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')
                                    .content,
                                'Accept': 'application/json'
                            },
                            body: formData
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
                                showAlert('success', data.message);
                                createCategoryModal.hide(); // Close the modal

                                // Add the new category to the select dropdown
                                const newOption = document.createElement('option');
                                newOption.value = data.category.id;
                                newOption.textContent = data.category.name;
                                categorySelect.appendChild(newOption);

                                // Select the newly added category
                                categorySelect.value = data.category.id;

                                // Reset form inside modal
                                createCategoryForm.reset();
                            } else {
                                throw new Error(data?.message || 'Failed to create category');
                            }
                        })
                        .catch(error => {
                            showAlert('danger', `Failed to create category: ${error.message}`);
                            // You might want to show the error inside the modal as well
                            categoryNameError.textContent = `Error: ${error.message}`;
                        })
                        .finally(() => {
                            saveCategoryBtn.innerHTML = originalBtnHtml;
                            saveCategoryBtn.disabled = false;
                        });
                });

                // Clear input and error message when modal is hidden
                document.getElementById('createCategoryModal').addEventListener('hidden.bs.modal', function() {
                    createCategoryForm.reset();
                    categoryNameError.textContent = '';
                });
            }

            // Helper function to display alerts
            function showAlert(type, message) {
                const alertId = 'alert-' + Date.now();
                const alertHtml = `
                    <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                        ${message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
                alertContainer.insertAdjacentHTML('afterbegin', alertHtml); // Insert at the top

                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    const alertElement = document.getElementById(alertId);
                    if (alertElement) {
                        const bsAlert = new bootstrap.Alert(alertElement);
                        bsAlert.close();
                    }
                }, 5000);
            }
        });
    </script>
</body>

</html>
