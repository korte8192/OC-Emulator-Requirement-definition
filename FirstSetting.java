/* 2.do_firstSetting(引数はこちらもUserInputと同じ)
メソッドにgeneratemasterへの通信在り
kotlin内での入力データをいれてjsonとしてpythonへの通信を送る */

import java.util.HashMap;
import java.util.Map;
import retrofit2.Response;

class FirstSetting{
    String user_id;
    String memo;
    String name;
    String firstP;
    String secondP;
    String talkstyle
    String style
    String personality;
    String iine;
    String weakness;
    String good;
    String suki;
    String kirai;
    String traumatic;
    String most_strong_ep;
    String user;
    String user_distance;
    String role;
    String str_val;
    String int_val;
    String pow_val;
    String sp;

    UserInput(String user_id,String memo,String name,String firstP,String secondP,String talkstyle,String style,String personality,String iine,String weakness,String good,String suki,String kirai,String traumatic,String most_strong_ep,String user,String user_distance,String role,String str_val,String int_val,String pow_val,String sp
    ) {
        this.user_id = user_id;
        this.memo = memo;
        this.name = name;
        this.firstP = firstP;
        this.secondP = secondP;
        this.talkstyle = talkstyle;
        this.style = style;
        this.personality = personality;
        this.iine = iine;
        this.weakness = weakness;
        this.good = good;
        this.suki = suki;
        this.kirai = kirai;
        this.traumatic = traumatic;
        this.most_strong_ep = most_strong_ep;
        this.user = user;
        this.user_distance = user_distance;
        this.role = role;
        this.str_val = str_val;
        this.int_val = int_val;
        this.pow_val = pow_val;
        this.sp = sp;
    }
    Map<String,String> do_firstSetting(){
        try{
            Response<MasterResponse> response=RetrofitClient.getApiService().generateMaster(this).execute();
            if (response.isSuccessful() && response.body() != null) {
                return response.body().master_data; // Mapをそのまま返す
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return new HashMap<>();
    }

}