# the network is one vpc with two public subnets in two availability zones
# there is no nat gateway on purpose because the machines sit in public subnets
# this keeps the demo cheap

# ask aws which availability zones we can use
data "aws_availability_zones" "available" {
  state = "available"
}

# our own private network in aws
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "lostfound-vpc" }
}

# the door between our network and the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "lostfound-igw" }
}

# one public subnet for each address range in the list
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  # the elb tag tells kubernetes to put public load balancers in these subnets
  tags = {
    Name                                        = "lostfound-public-${count.index + 1}"
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# send all internet traffic through the internet gateway
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "lostfound-public-rt" }
}

# link each public subnet to the route table above
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
