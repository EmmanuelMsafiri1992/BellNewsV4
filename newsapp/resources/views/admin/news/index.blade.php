<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manage News</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
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
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .news-card {
            height: 100%;
            overflow: hidden;
        }

        .news-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 10px;
            transition: all 0.3s ease;
        }

        .news-image:hover {
            transform: scale(1.05);
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

        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            border: none;
            border-radius: 20px;
            padding: 8px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }

        .btn-warning {
            background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
            border: none;
            border-radius: 20px;
            padding: 8px 20px;
            font-weight: 600;
            color: white;
            transition: all 0.3s ease;
        }

        .btn-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(254, 202, 87, 0.4);
            color: white;
        }

        .btn-info {
            background: linear-gradient(135deg, #3742fa 0%, #2f3542 100%);
            border: none;
            border-radius: 20px;
            padding: 8px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            color: white;
        }

        .btn-info:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(55, 66, 250, 0.4);
            color: white;
        }

        .welcome-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
        }

        .alert {
            border-radius: 10px;
            border: none;
        }

        .badge {
            font-size: 0.75rem;
            padding: 6px 12px;
            border-radius: 20px;
        }

        .badge-published {
            background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
        }

        .badge-draft {
            background: linear-gradient(135deg, #ffa502 0%, #ff6348 100%);
        }

        .news-meta {
            font-size: 0.875rem;
            color: #6c757d;
        }

        .action-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .search-box {
            border-radius: 25px;
            border: 2px solid #e9ecef;
            padding: 12px 20px;
            transition: all 0.3s ease;
        }

        .search-box:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }

        .filter-select {
            border-radius: 25px;
            border: 2px solid #e9ecef;
            padding: 12px 20px;
            transition: all 0.3s ease;
        }

        .filter-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }

        .no-news {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }

        .no-news i {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }

        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }

        .stats-number {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .pagination-wrapper {
            display: flex;
            justify-content: center;
            margin-top: 30px;
        }

        .modal-content {
            border-radius: 15px;
            border: none;
        }

        .modal-header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
            border-radius: 15px 15px 0 0;
        }

        /* Styles for the table in the second HTML */
        .table {
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .table thead th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom: none;
            padding: 15px;
        }

        .table tbody tr:nth-child(even) {
            background-color: #f2f2f2;
        }

        .table tbody tr:hover {
            background-color: #e9ecef;
            cursor: pointer;
        }

        /* Carousel specific styles */
        .carousel-item img {
            max-height: 500px;
            /* Adjust as needed */
            width: 100%;
            object-fit: contain;
            /* Keeps aspect ratio and fits within bounds */
        }
    </style>
</head>

<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 p-0">
                <div class="sidebar p-3">
                    <div class="text-center mb-4">
                        <h4><i class="fas fa-tachometer-alt"></i> Admin Panel</h4>
                    </div>
                    <nav class="nav flex-column">
                        <a class="nav-link" href="{{ route('admin.dashboard') }}">
                            <i class="fas fa-home me-2"></i> Dashboard
                        </a>
                        <a class="nav-link active" href="{{ route('admin.news.index') }}">
                            <i class="fas fa-newspaper me-2"></i> All News
                        </a>
                        <a class="nav-link" href="{{ route('admin.settings') }}">
                            <i class="fas fa-cog me-2"></i> Settings
                        </a>
                        <hr class="my-3">
                        <a class="nav-link" href="#"
                            onclick="event.preventDefault(); document.getElementById('logout-form').submit();">
                            <i class="fas fa-sign-out-alt me-2"></i> Logout
                        </a>
                        <form id="logout-form" action="{{ route('logout') }}" method="POST" style="display: none;">
                            @csrf
                        </form>
                    </nav>
                </div>
            </div>

            <div class="col-md-10 main-content p-4">
                <div class="welcome-section">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-newspaper"></i> Manage News Articles</h1>
                            <p class="mb-0">Create, edit, and manage all your news content</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="text-white-50">
                                <i class="fas fa-user"></i> {{ Auth::user()->name }}
                            </div>
                        </div>
                    </div>
                </div>

                @if (session('success'))
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <i class="fas fa-check-circle me-2"></i>{{ session('success') }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                @endif

                @if (session('error'))
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>{{ session('error') }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                @endif

                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="stats-card">
                            <div class="stats-number">{{ $news->count() }}</div>
                            <div>Total Articles</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card">
                            <div class="stats-number">{{ $news->where('status', 'published')->count() }}</div>
                            <div>Published</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card">
                            <div class="stats-number">{{ $news->where('status', 'draft')->count() }}</div>
                            <div>Drafts</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stats-card">
                            <div class="stats-number">{{ $news->where('created_at', '>=', today())->count() }}</div>
                            <div>Today</div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-6">
                        <a href="{{ route('admin.news.create') }}" class="btn btn-primary">
                            <i class="fas fa-plus me-2"></i> Add New Article
                        </a>
                    </div>
                    <div class="col-md-6">
                        <div class="row">
                            <div class="col-md-8">
                                <input type="text" class="form-control search-box" id="searchInput"
                                    placeholder="Search articles..." onkeyup="filterTable()">
                            </div>
                            <div class="col-md-4">
                                <select class="form-select filter-select" id="statusFilter" onchange="filterTable()">
                                    <option value="">All Status</option>
                                    <option value="published">Published</option>
                                    <option value="draft">Draft</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                @if ($news->count() > 0)
                    <div class="card">
                        <div class="card-body">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Title</th>
                                        <th>Category</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="newsTableBody">
                                    @foreach ($news as $item)
                                        <tr class="news-item" data-title="{{ strtolower(strip_tags($item->title)) }}"
                                            data-status="{{ $item->status ?? 'published' }}">
                                            {{-- **FIXED**: Use {!! !!} to render HTML formatting in the title --}}
                                            <td>{!! Str::limit($item->title, 60) !!}</td>
                                            <td>{{ ucfirst($item->category->name ?? 'General') }}</td>
                                            <td><span
                                                    class="badge {{ $item->status == 'published' ? 'badge-published' : 'badge-draft' }}">{{ ucfirst($item->status) }}</span>
                                            </td>
                                            <td>{{ $item->created_at->format('M d, Y') }}</td>
                                            <td>
                                                <div class="action-buttons">
                                                    {{-- Updated: Pass all image URLs as JSON to a data attribute, ensuring path is relative to storage/app/public --}}
                                                    <button type="button" class="btn btn-info btn-sm view-images-btn"
                                                        data-bs-toggle="modal" data-bs-target="#imageModal"
                                                        data-images="{{ json_encode(
                                                            $item->images->pluck('url')->map(function ($url) {
                                                                    if (Str::startsWith($url, 'public/')) {
                                                                        return substr($url, 7);
                                                                    } elseif (Str::startsWith($url, 'storage/')) {
                                                                        return substr($url, 8);
                                                                    }
                                                                    return $url;
                                                                })->toArray(),
                                                        ) }}">
                                                        <i class="fas fa-eye"></i>
                                                    </button>
                                                    <a href="{{ route('admin.news.edit', $item->id) }}"
                                                        class="btn btn-warning btn-sm">
                                                        <i class="fas fa-edit"></i>
                                                    </a>
                                                    <button type="button" class="btn btn-danger btn-sm"
                                                        onclick="confirmDelete({{ $item->id }}, '{{ addslashes(strip_tags($item->title)) }}')">
                                                        <i class="fas fa-trash"></i>
                                                    </button>
                                                    <form id="delete-form-{{ $item->id }}"
                                                        action="{{ route('admin.news.destroy', $item->id) }}"
                                                        method="POST" style="display: none;">
                                                        @csrf
                                                        @method('DELETE')
                                                    </form>
                                                </div>
                                            </td>
                                        </tr>
                                    @endforeach
                                </tbody>
                            </table>
                        </div>
                    </div>
                @else
                    <div class="no-news">
                        <i class="fas fa-newspaper"></i>
                        <h3>No News Articles Yet</h3>
                        <p>Start by creating your first news article!</p>
                        <a href="{{ route('admin.news.create') }}" class="btn btn-primary">
                            <i class="fas fa-plus me-2"></i> Create First Article
                        </a>
                    </div>
                @endif

                @if (method_exists($news, 'links'))
                    <div class="pagination-wrapper">
                        {{ $news->links() }}
                    </div>
                @endif
            </div>
        </div>
    </div>

    {{-- DELETE CONFIRMATION MODAL --}}
    <div class="modal fade" id="deleteModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="deleteModalLabel">
                        <i class="fas fa-exclamation-triangle"></i> Confirm Delete
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete this article?</p>
                    <p><strong id="articleTitle"></strong></p>
                    <p class="text-muted">This action cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                        <i class="fas fa-trash"></i> Delete Article
                    </button>
                </div>
            </div>
        </div>
    </div>

    {{-- IMAGE PREVIEW MODAL - UPDATED WITH CAROUSEL --}}
    <div class="modal fade" id="imageModal" tabindex="-1" aria-labelledby="imageModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="imageModalLabel">Image Preview</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    {{-- Bootstrap Carousel --}}
                    <div id="imageCarousel" class="carousel slide" data-bs-interval="false">
                        <div class="carousel-inner" id="carouselInner">
                            {{-- Images will be loaded here by JavaScript --}}
                        </div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#imageCarousel"
                            data-bs-slide="prev">
                            <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                            <span class="visually-hidden">Previous</span>
                        </button>
                        <button class="carousel-control-next" type="button" data-bs-target="#imageCarousel"
                            data-bs-slide="next">
                            <span class="carousel-control-next-icon" aria-hidden="true"></span>
                            <span class="visually-hidden">Next</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script>
        let deleteItemId = null; // Variable to store the ID of the item to be deleted

        // Function to show the delete confirmation modal
        function confirmDelete(itemId, title) {
            deleteItemId = itemId; // Store the ID
            document.getElementById('articleTitle').innerHTML = title; // Set the title in the modal, use innerHTML for safety
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
            deleteModal.show(); // Show the modal
        }

        // Event listener for the "Delete Article" button inside the modal
        document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
            if (deleteItemId) { // Ensure an ID is set
                document.getElementById('delete-form-' + deleteItemId).submit(); // Submit the correct form
            }
        });

        // Function to populate and show the image carousel modal
        function populateImageModal(images) {
            const carouselInner = document.getElementById('carouselInner');
            carouselInner.innerHTML = ''; // Clear previous images

            if (images && images.length > 0) {
                images.forEach((imageUrl, index) => {
                    const carouselItem = document.createElement('div');
                    carouselItem.classList.add('carousel-item');
                    if (index === 0) {
                        carouselItem.classList.add('active'); // First image is active
                    }

                    const img = document.createElement('img');
                    // Construct the URL directly by prepending '/storage/'
                    img.src = `/storage/${imageUrl}`; // THIS IS THE KEY CHANGE
                    img.classList.add('d-block', 'w-100');
                    img.alt = `News Image ${index + 1}`;

                    carouselItem.appendChild(img);
                    carouselInner.appendChild(carouselItem);
                });

                // Initialize Bootstrap Carousel if there's more than one image
                const imageCarousel = new bootstrap.Carousel(document.getElementById('imageCarousel'), {
                    interval: false // Disable auto-sliding
                });

                // Show carousel controls only if there are multiple images
                document.querySelector('.carousel-control-prev').style.display = images.length > 1 ? 'block' : 'none';
                document.querySelector('.carousel-control-next').style.display = images.length > 1 ? 'block' : 'none';

            } else {
                carouselInner.innerHTML =
                    '<div class="carousel-item active"><p class="text-center py-5">No images available for this article.</p></div>';
                // Hide controls if no images
                document.querySelector('.carousel-control-prev').style.display = 'none';
                document.querySelector('.carousel-control-next').style.display = 'none';
            }
        }

        // Event delegation for "View Image" buttons
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.view-images-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const imagesData = JSON.parse(this.dataset.images);
                    populateImageModal(imagesData);
                });
            });

            // Auto-dismiss alerts after 5 seconds
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(function(alert) {
                setTimeout(function() {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 5000);
            });
        });


        // Filter and search functionality for the table
        function filterTable() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const statusFilter = document.getElementById('statusFilter').value;
            const newsTableBody = document.getElementById('newsTableBody');
            const newsItems = newsTableBody.querySelectorAll('.news-item');
            let visibleCount = 0;

            newsItems.forEach(function(item) {
                const title = item.getAttribute('data-title');
                const status = item.getAttribute('data-status');

                const matchesSearch = title.includes(searchTerm);
                const matchesStatus = statusFilter === '' || status === statusFilter;

                if (matchesSearch && matchesStatus) {
                    item.style.display = ''; // Show the row
                    visibleCount++;
                } else {
                    item.style.display = 'none'; // Hide the row
                }
            });

            // Show/hide no results message
            let noResultsRow = document.getElementById('noResultsRow');
            if (visibleCount === 0 && (searchTerm !== '' || statusFilter !== '')) {
                if (!noResultsRow) {
                    noResultsRow = newsTableBody.insertRow();
                    noResultsRow.id = 'noResultsRow';
                    noResultsRow.innerHTML = `
                        <td colspan="5" class="text-center py-5 text-muted">
                            <i class="fas fa-search fa-3x mb-3"></i>
                            <h4>No articles found</h4>
                            <p>Try adjusting your search or filter criteria.</p>
                        </td>
                    `;
                }
            } else if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    </script>
</body>

</html>
