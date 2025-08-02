# Use the official PHP image with Apache as the base
FROM php:8.2-apache

# Set the working directory inside the container
WORKDIR /var/www/html

# Copy the entire application source code into the container
COPY . /var/www/html

# Install system dependencies and PHP extensions
# The `&& \` at the end of each line allows chaining multiple commands
# on a single RUN instruction, which is more efficient for Docker layers.
RUN apt-get update && \
    apt-get install -y \
       libzip-dev \
       unzip \
       git \
       libpng-dev \
       libjpeg-dev \
       libfreetype6-dev \
       iproute2 \
    && docker-php-ext-configure gd \
         --with-freetype=/usr/include/ \
         --with-jpeg=/usr/include/ \
    && docker-php-ext-install \
         zip \
         pdo \
         pdo_mysql \
         gd \
    && rm -rf /var/lib/apt/lists/*

# Install Composer globally
RUN curl -sS https://getcomposer.org/installer \
      | php -- --install-dir=/usr/local/bin --filename=composer

# Install Composer dependencies and link storage
RUN composer install --no-interaction --prefer-dist --optimize-autoloader \
 && php artisan storage:link

# Copy the custom entrypoint script into the container and make it executable
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose the ports for the web server and Vite's HMR
EXPOSE 8000
EXPOSE 5173

# Set the custom entrypoint script to run first
ENTRYPOINT ["docker-entrypoint.sh"]

# Set the default command to start the Laravel development server
# This will be executed by the entrypoint script
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8000"]
