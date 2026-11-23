/* 整理すると、結局kotlin→pythonはuserinput(初期設定のみ)とuserid,usermessage(/chatを実行の際に引数にするなどする)でもらうものは返答のみ。それで入力するものはuserinputとログイン時にuserid、chatのときに会話内容ってかんじかなその場合作るべきjavaの型は私的には
1.chat(引数はpythonと同じ userid,message)
メソッドはpythonへの通信をするdo_chat()
返り値はString必ずkotlinに渡す際は値が返ってくるまでのラグを考慮してwhile文ではなく
lifecycleScope.launch(Dispatchers.IO)をつかう
 */
import retrofit2.Response;

public class Chat{
    String userid;
    String message;

    Chat(String u,String m){
        userid=u;
        message=m;
    }

    String do_chat(){
        try {
            Response<ChatResponse> response=RetrofitClient.getApiService().sendMessage(this).execute();
            if (response.isSuccessful() && response.body() != null) {
                return response.body().reply;
            } else {
                return "サーバーエラー: " + response.code();
            }
        } catch (Exception e) {
            return "通信エラー: " + e.getMessage();
        }
    }
}