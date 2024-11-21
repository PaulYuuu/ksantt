sudo vgcreate --shared kubesan-vg /dev/sdb

sudo lvmdevices --devicesfile kubesan-vg --adddev /dev/sdb
sudo vgchange --devicesfile kubesan-vg --lock-start
sudo vgs --devicesfile kubesan-vg
