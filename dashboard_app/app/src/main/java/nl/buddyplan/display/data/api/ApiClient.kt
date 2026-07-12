package nl.buddyplan.display.data.api

import android.content.Context
import nl.buddyplan.display.AppPreferences
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private val clients = mutableMapOf<String, BuddyplanApi>()

    fun getApi(context: Context): BuddyplanApi {
        val baseUrl = AppPreferences.getServerUrl(context.applicationContext).trimEnd('/') + "/"
        return clients.getOrPut(baseUrl) {
            val authInterceptor = Interceptor { chain ->
                val token = AppPreferences.getAuthToken(context.applicationContext)
                val requestBuilder = chain.request().newBuilder()
                    .header("Cache-Control", "no-cache")
                    .header("Pragma", "no-cache")
                if (!token.isNullOrBlank()) {
                    requestBuilder.header("Authorization", "Bearer $token")
                }
                chain.proceed(requestBuilder.build())
            }

            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
            }

            val okHttp = OkHttpClient.Builder()
                .addInterceptor(authInterceptor)
                .addInterceptor(logging)
                .connectTimeout(5, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build()

            Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(okHttp)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(BuddyplanApi::class.java)
        }
    }

    fun invalidate() {
        clients.clear()
    }
}
