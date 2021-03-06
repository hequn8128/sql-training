
from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.table import StreamTableEnvironment, DataTypes, EnvironmentSettings
from pyflink.table.descriptors import Schema, Kafka, Json, Rowtime

s_env = StreamExecutionEnvironment.get_execution_environment()
s_env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
s_env.set_parallelism(1)

# use blink table planner
st_env = StreamTableEnvironment\
    .create(s_env, environment_settings=EnvironmentSettings
            .new_instance()
            .in_streaming_mode()
            .use_blink_planner().build())

st_env \
    .connect(  # declare the external system to connect to
        Kafka()
            .version("0.11")
            .topic("Rides")
            .start_from_earliest()
            .property("zookeeper.connect", "zookeeper:2181")
            .property("bootstrap.servers", "kafka:9092")) \
    .with_format(  # declare a format for this system
        Json()
            .fail_on_missing_field(True)
            .schema(DataTypes.ROW([
                DataTypes.FIELD("rideId", DataTypes.BIGINT()),
                DataTypes.FIELD("isStart", DataTypes.BOOLEAN()),
                DataTypes.FIELD("eventTime", DataTypes.TIMESTAMP()),
                DataTypes.FIELD("lon", DataTypes.FLOAT()),
                DataTypes.FIELD("lat", DataTypes.FLOAT()),
                DataTypes.FIELD("psgCnt", DataTypes.INT()),
                DataTypes.FIELD("taxiId", DataTypes.BIGINT())]))) \
    .with_schema(  # declare the schema of the table
        Schema()
            .field("rideId", DataTypes.BIGINT())
            .field("taxiId", DataTypes.BIGINT())
            .field("isStart", DataTypes.BOOLEAN())
            .field("lon", DataTypes.FLOAT())
            .field("lat", DataTypes.FLOAT())
            .field("psgCnt", DataTypes.INT())
            .field("rideTime", DataTypes.TIMESTAMP())
            .rowtime(
            Rowtime()
                .timestamps_from_field("eventTime")
                .watermarks_periodic_bounded(60000))) \
    .in_append_mode() \
    .register_table_source("source")

st_env \
    .connect(  # declare the external system to connect to
        Kafka()
            .version("0.11")
            .topic("TempResults")
            .property("zookeeper.connect", "zookeeper:2181")
            .property("bootstrap.servers", "kafka:9092")) \
    .with_format(  # declare a format for this system
        Json()
            .fail_on_missing_field(True)
            .schema(DataTypes.ROW([
                DataTypes.FIELD("rideId", DataTypes.BIGINT()),
                DataTypes.FIELD("taxiId", DataTypes.BIGINT()),
                DataTypes.FIELD("isStart", DataTypes.BOOLEAN()),
                DataTypes.FIELD("lon", DataTypes.FLOAT()),
                DataTypes.FIELD("lat", DataTypes.FLOAT()),
                DataTypes.FIELD("psgCnt", DataTypes.INT()),
                DataTypes.FIELD("rideTime", DataTypes.TIMESTAMP())
                ])))\
    .with_schema(  # declare the schema of the table
        Schema()
            .field("rideId", DataTypes.BIGINT())
            .field("taxiId", DataTypes.BIGINT())
            .field("isStart", DataTypes.BOOLEAN())
            .field("lon", DataTypes.FLOAT())
            .field("lat", DataTypes.FLOAT())
            .field("psgCnt", DataTypes.INT())
            .field("rideTime", DataTypes.TIMESTAMP()))\
    .in_append_mode() \
    .register_table_sink("sink")

st_env.from_path("source").select("*").insert_into("sink")

st_env.execute("from_kafka_to_kafka")