terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.7.0"
    }
  }
}

provider "aws" {
  region     = "us-east-1"
  access_key = "A"
  secret_key = "V"
}

#Creating a VPC
resource "aws_vpc" "nebula_prod_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "nebula_vpc"
  }

}
#2 Subnet within my prod VPC
resource "aws_subnet" "nebula_private_subnet" {
  vpc_id     = aws_vpc.nebula_prod_vpc.id
  cidr_block = "10.0.1.0/24"

  tags = {
    Name = "nebula_main_subnet"
  }
}
resource "aws_subnet" "nebula_public_subnet" {
  vpc_id     = aws_vpc.nebula_prod_vpc.id
  cidr_block = "10.0.2.0/24"

  tags = {
    Name = "nebula_secondary_subnet"
  }
}
#Internet Gateway for production VPC
resource "aws_internet_gateway" "nebula_gateway" {
  vpc_id = aws_vpc.nebula_prod_vpc.id

  tags = {
    Name = "nebula_gateway"
  }
}

#A route table for the VPC created
resource "aws_route_table" "nebula_route_table" {
  vpc_id = aws_vpc.nebula_prod_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.nebula_gateway.id
  }

  
  tags = {
    Name = "production_routes"
  }
}
#Route table association to link the route table to the subnet
resource "aws_route_table_association" "nebula_rt_links" {
  subnet_id      = aws_subnet.nebula_public_subnet.id
  route_table_id = aws_route_table.nebula_route_table.id
}

#Security group for the created resources
resource "aws_security_group" "allow_web_traffic" {
  name        = "allow_web_traffic"
  description = "Allow TLS inbound traffic for prod"
  vpc_id      = aws_vpc.nebula_prod_vpc.id

  ingress {
    description      = "HTTPS traffic"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "HTTP traffic"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  ingress {
    description      = "SSH traffic"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "allow_all_web_traffic"
  }
}

#A network interface to link an IP to the created subnet.Private IP address for the host
resource "aws_network_interface" "provisioned_resources" {
  subnet_id       = aws_subnet.nebula_public_subnet.id
  private_ips     = ["10.0.1.50"]
  security_groups = [aws_security_group.allow_web_traffic.id]

}

#Creating an Ubuntu server instance (EC2)
resource "aws_instance" "web_server_prod" {
  ami               = "ami-053b0d53c279acc90"
  instance_type     = "t2.micro"
  availability_zone = "us-east-1a"

  network_interface {
    device_index         = 0
    network_interface_id = aws_network_interface.provisioned_resources.id
  }

  tags = {
    Name = "Prod_web_server"
  }
}

resource "aws_s3_bucket" "nebulaprojectbucket9876" {
    bucket = "nebulaprojectbucket9876"
    tags = {
      Environment = "production" 
    } 
  
}
resource "aws_s3_bucket_lifecycle_configuration" "nebulaprojectbucket9876" {
    bucket = aws_s3_bucket.nebulaprojectbucket9876.id
    
    rule {
        id = "uploads"
        expiration {
          days = 90
        }        
        filter {
          and {
            prefix = "uploads/"
          }
        }
        status = "Enabled"
        transition {
          days =  60
          storage_class = "GLACIER"
        }
        
    }  
}

resource "aws_cloudwatch_metric_alarm" "nebula_metrics" {
  alarm_name                = "nebula_metrics"
  comparison_operator       = "GreaterThanOrEqualToThreshold"
  evaluation_periods        = 2
  metric_name               = "CPUUtilization"
  namespace                 = "AWS/EC2"
  period                    = 120
  statistic                 = "Average"
  threshold                 = 80
  alarm_description         = "This metric monitors ec2 cpu utilization"
  insufficient_data_actions = []
}