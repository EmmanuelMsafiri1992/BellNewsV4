{{-- resources/views/admin/sidebar.blade.php (Example snippet) --}}
<div class="d-flex flex-column p-3 text-white sidebar" style="width: 280px;">
    <a href="/" class="d-flex align-items-center mb-3 mb-md-0 me-md-auto text-white text-decoration-none">
        <i class="fas fa-tachometer-alt me-2"></i>
        <span class="fs-4">{{ __('Admin Panel') }}</span>
    </a>
    <hr>
    <ul class="nav nav-pills flex-column mb-auto">
        <li class="nav-item">
            <a href="{{ route('admin.dashboard') }}"
                class="nav-link text-white {{ request()->routeIs('admin.dashboard') ? 'active' : '' }}"
                aria-current="page">
                <i class="fas fa-home me-2"></i>
                {{ __('Dashboard') }}
            </a>
        </li>
        <li>
            <a href="{{ route('admin.news.index') }}"
                class="nav-link text-white {{ request()->routeIs('admin.news.*') ? 'active' : '' }}">
                <i class="fas fa-newspaper me-2"></i>
                {{ __('All News') }}
            </a>
        </li>
        <li>
            <a href="{{ route('admin.settings') }}"
                class="nav-link text-white {{ request()->routeIs('admin.settings') ? 'active' : '' }}">
                <i class="fas fa-cogs me-2"></i>
                {{ __('Settings') }}
            </a>
        </li>
        <li class="nav-item">
    <a class="nav-link {{ Request::routeIs('admin.users.*') ? 'active' : '' }}" href="{{ route('admin.users.index') }}">
        <i class="fas fa-users me-2"></i>
        Users
    </a>
</li>
        {{-- ADD THIS NEW SECTION FOR LICENSES (ONLY VISIBLE TO SUPERADMIN) --}}
        @if (Auth::user()->isSuperAdmin())
            <li>
                <a href="{{ route('admin.licenses.index') }}"
                    class="nav-link text-white {{ request()->routeIs('admin.licenses.*') ? 'active' : '' }}">
                    <i class="fas fa-key me-2"></i>
                    {{ __('Licenses') }}
                </a>
            </li>
        @endif
    </ul>
    <hr>
    <div class="dropdown">
        <a href="#" class="d-flex align-items-center text-white text-decoration-none dropdown-toggle"
            id="dropdownUser1" data-bs-toggle="dropdown" aria-expanded="false">
            <img src="https://github.com/mdo.png" alt="" width="32" height="32"
                class="rounded-circle me-2">
            <strong>{{ Auth::user()->name }}</strong>
        </a>
        <ul class="dropdown-menu dropdown-menu-dark text-small shadow" aria-labelledby="dropdownUser1">
            <li><a class="dropdown-item" href="{{ route('admin.settings') }}">{{ __('Settings') }}</a></li>
            <li>
                <hr class="dropdown-divider">
            </li>
            <li>
                <a class="dropdown-item" href="{{ route('logout') }}"
                    onclick="event.preventDefault(); document.getElementById('logout-form').submit();">
                    {{ __('Logout') }}
                </a>
                <form id="logout-form" action="{{ route('logout') }}" method="POST" class="d-none">
                    @csrf
                </form>
            </li>
        </ul>
    </div>
</div>
