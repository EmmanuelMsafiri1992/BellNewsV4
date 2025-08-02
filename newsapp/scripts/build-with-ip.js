// scripts/build-with-ip.js
const { execSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function getLocalIP() {
  try {
    // Method 1: Try to get IP from default route
    const routeOutput = execSync('ip route get 1.1.1.1 2>/dev/null || echo ""', { encoding: 'utf8' });
    const ipMatch = routeOutput.match(/src (\S+)/);
    if (ipMatch) {
      return ipMatch[1];
    }
  } catch (error) {
    // Continue to next method
  }

  try {
    // Method 2: Check hostname -I
    const hostnameOutput = execSync('hostname -I 2>/dev/null || echo ""', { encoding: 'utf8' });
    const ip = hostnameOutput.trim().split(' ')[0];
    if (ip && ip !== '') {
      return ip;
    }
  } catch (error) {
    // Continue to next method
  }

  // Method 3: Use Node.js network interfaces
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }

  return 'localhost';
}

function updateEnvFile(ip) {
  const envPath = path.join(process.cwd(), '.env');

  if (!fs.existsSync(envPath)) {
    console.log('Warning: .env file not found, creating minimal configuration');
    const minimalEnv = `APP_URL=http://${ip}:8000\nVITE_API_BASE_URL=http://${ip}:8000\n`;
    fs.writeFileSync(envPath, minimalEnv);
    return;
  }

  let envContent = fs.readFileSync(envPath, 'utf8');

  // Update APP_URL
  if (envContent.includes('APP_URL=')) {
    envContent = envContent.replace(/^APP_URL=.*/m, `APP_URL=http://${ip}:8000`);
  } else {
    envContent += `\nAPP_URL=http://${ip}:8000`;
  }

  // Update VITE_API_BASE_URL
  if (envContent.includes('VITE_API_BASE_URL=')) {
    envContent = envContent.replace(/^VITE_API_BASE_URL=.*/m, `VITE_API_BASE_URL=http://${ip}:8000`);
  } else {
    envContent += `\nVITE_API_BASE_URL=http://${ip}:8000`;
  }

  fs.writeFileSync(envPath, envContent);
  console.log(`Updated .env file with IP: ${ip}`);
}

function buildAssets() {
  console.log('Building frontend assets...');

  try {
    // Install dependencies if needed
    if (!fs.existsSync('node_modules')) {
      console.log('Installing npm dependencies...');
      execSync('npm ci', { stdio: 'inherit' });
    }

    // Build the assets
    execSync('vite build', { stdio: 'inherit' });
    console.log('Frontend assets built successfully!');

  } catch (error) {
    console.error('Build failed:', error.message);
    process.exit(1);
  }
}

function main() {
  console.log('=== Dynamic Frontend Build ===');

  // Get current IP
  const currentIP = getLocalIP();
  console.log(`Detected IP address: ${currentIP}`);

  // Set environment variable for Vite
  process.env.HOST_IP = currentIP;

  // Update .env file
  updateEnvFile(currentIP);

  // Build assets
  buildAssets();

  console.log('=== Build completed ===');
}

// Run if this script is executed directly
if (require.main === module) {
  main();
}

module.exports = { getLocalIP, updateEnvFile, buildAssets };
