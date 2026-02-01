# Check build dependencies on Windows
# Prints guidance and tries to detect GCC and Arduino CLI

Write-Host "Checking build dependencies..."
$gcc = Get-Command gcc -ErrorAction SilentlyContinue
$arduino = Get-Command arduino-cli -ErrorAction SilentlyContinue

if ($gcc) {
    Write-Host "gcc found: $($gcc.Path)"
} else {
    Write-Host "gcc not found. If you want to run clang/gcc checks locally, install MinGW-w64 or MSYS2."
    Write-Host "Suggested (MSYS2):"
    Write-Host "  - Install MSYS2 from https://www.msys2.org/"
    Write-Host "  - Then: pacman -S mingw-w64-x86_64-gcc"
}

if ($arduino) {
    Write-Host "arduino-cli found: $($arduino.Path)"
    Write-Host "You can build the firmware with: arduino-cli compile --fqbn arduino:avr:mega arduino_firmware"
} else {
    Write-Host "arduino-cli not found. For Windows, install Arduino CLI to compile the Arduino project:" 
    Write-Host "  https://arduino.github.io/arduino-cli/latest/installation/"
}

Write-Host "Helper: use tools/build_firmware.py to attempt a local build with fallbacks."
