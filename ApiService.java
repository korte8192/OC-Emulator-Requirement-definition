import java.util.Map;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.POST;

class MasterResponse{
    String status;
    Map<String,String> master_data;
}

class ChatResponse{
    String status;
    String reply;
}

public interface ApiService {
    @POST("generate-master")
    Call<MasterResponse> generateMaster(@Body FirstSetting setting);

    @POST("chat")
    Call<ChatResponse> sendMessage(@Body Chat chat);
}