data "yandex_compute_image" "image" {
    family = "container-optimized-image"
}


resource "yandex_compute_instance" "compute" {
    name = "${local.resource_prefix}-compute"
    platform_id = "standard-v2"
    boot_disk {
      mode = "READ_WRITE"
      initialize_params {
        image_id = data.yandex_compute_image.image.id
        size = 30
      }
    }

    network_interface {
      subnet_id = yandex_vpc_subnet.subnet.id
      nat = true
      nat_ip_address = yandex_vpc_address.address.external_ipv4_address[0].address
      
    }
    allow_stopping_for_update = true

    scheduling_policy {
      preemptible = false
    }

    resources {
      cores = 2
      memory = 2
      core_fraction = 5
    }

    metadata = {
      docker-compose = file("${path.root}/../docker-compose.yaml")
      ssh-keys = "ubuntu:${file("~/.ssh/florin.pub")}"
    }
}

resource "yandex_vpc_network" "vpc" {
    name = "${local.resource_prefix}-network"
    
}

resource "yandex_vpc_subnet" "subnet" {
    name = "${local.resource_prefix}-subnet"
    network_id = yandex_vpc_network.vpc.id
    v4_cidr_blocks = ["192.168.10.0/24"]

}

resource "yandex_vpc_address" "address" {
    name = "${local.resource_prefix}-address"

    external_ipv4_address {
      zone_id = local.zone
    }
  
}
