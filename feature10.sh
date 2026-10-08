touch ~/report.txt
echo "Report generated on $(date)" > ~/report.txt
echo "User: $(whoami)" >> ~/report.txt
echo "Raspberry Name: $(hostname)" >> ~/report.txt
echo "Report saved to ~/report.txt"