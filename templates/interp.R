library(ggplot2)
library(gstat)
library(sp)
library(maptools)
library(automap)
require(RSQLite)
args <- commandArgs(trailingOnly = TRUE)
etretm_file = args[1]
estado = args[2]
arquivo_csv = args[3]
interpolacao = args[4]
server_path = args[5]
output_path = args[6]
db_path = args[7]

print(output_path)
print(arquivo_csv)

runsql <- function(sql, dbname=db_path){
  driver <- dbDriver("SQLite")
  connect <- dbConnect(driver, dbname=dbname);
  closeup <- function(){
    sqliteCloseConnection(connect)
    sqliteCloseDriver(driver)
  }
  dd <- tryCatch(dbGetQuery(connect, sql), finally=closeup)
  return(dd)
}

sql_query = paste0("select sigla,shapefile from estado where sigla = '",estado,"'")
df = runsql(sql_query)
df$shapefile = paste0(server_path,"/",df$shapefile)
shape = readShapePoly(df$shapefile)
latmin = min(shape@data$LAT1)
latmax = max(shape@data$LAT1)
longmin = min(shape@data$LONG1)
longmax = max(shape@data$LONG1)

etretm = read.table(file=etretm_file,header=TRUE,sep=",")
etretm = etretm[complete.cases(etretm),]
etretm$x <- etretm$longitude  # define x & y as longitude and latitude
etretm$y <- etretm$latitude
coordinates(etretm) = ~x + y
y.range <- as.numeric(c(latmin,latmax))  # min/max latitude of the interpolation area
x.range <- as.numeric(c(longmin,longmax))  # min/max longitude of the interpolation area
grd <- expand.grid(x = seq(from = x.range[1], to = x.range[2], by = 0.1), y = seq(from = y.range[1],to = y.range[2], by = 0.1))
coordinates(grd) <- ~x + y
gridded(grd) <- TRUE
saida = paste0(output_path,"/",arquivo_csv)

#############################################IDW###########################################################
interpolacao_idw = function(dadoscol) {
   dadosinter = etretm
   colnames(dadosinter@data)[colnames(dadosinter@data) == dadoscol] = 'dados'
   idw <- idw(formula = as.formula("dados~1"), locations = dadosinter, newdata = grd)  # apply idw model for the data
   idw.output = as.data.frame(idw)  # output is defined as a data table
   return (idw.output)
}

##########################################KRIGING##########################################################
interpolacao_krig = function(dadoscol) {
   dadosinter = etretm
   colnames(dadosinter@data)[colnames(dadosinter@data) == dadoscol] = 'dados'
   vgm = autofitVariogram(dados~1,dadosinter)
   k = krige(as.formula("dados~1"), dadosinter, newdata=grd, model=vgm$var_model, debug.level=0, nmax=32)
   k = as.data.frame(k)
   return (k)
}
print("oi")
if(interpolacao=="krig" || interpolacao=="idw" ){
  for(i in 4:ncol(etretm@data)) {
     if(interpolacao=="krig")
        decendio_interpolado = interpolacao_krig(colnames(etretm@data)[i])
     else if(interpolacao=="idw")
        decendio_interpolado = interpolacao_idw(colnames(etretm@data)[i])
     if(i==4) {
        output = data.frame(decendio_interpolado[1],decendio_interpolado[2])
        colnames(output) = c("longitude","latitude")
     }
     output = cbind(output,decendio_interpolado[3])
     colnames(output)[i-1] = paste0("dec",as.character(i-3))
  }
} else {
  for(i in 4:ncol(etretm@data)) {
    if(i==4) {
      output = data.frame(etretm@data[3],etretm@data[2])
      colnames(output) = c("longitude","latitude")
    }
    output = cbind(output,etretm@data[i])
    colnames(output)[i-1] = paste0("dec",as.character(i-3))
  }
}
write.table(output,file=saida,sep=",",row.names=FALSE)