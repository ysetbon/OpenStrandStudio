@echo off
echo Starting Curvature Bias Control Test...
echo.
echo ============================================================
echo INSTRUCTIONS:
echo 1. Enable Settings ^> General ^> "Enable third control point"
echo 2. Enable Settings ^> General ^> "Enable curvature bias controls"
echo 3. Create a strand or use the test strand
echo 4. Move the center (square) control point to lock it
echo 5. Two bias control squares will appear
echo 6. Drag them horizontally to adjust curve bias!
echo ============================================================
echo.
python test_bias_control.py
pause