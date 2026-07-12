package nl.buddyplan.display.data.api

import nl.buddyplan.display.data.DashboardData
import nl.buddyplan.display.data.PersonCalendar
import nl.buddyplan.display.data.WeekDay
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface BuddyplanApi {

    @GET("api/dashboard/etag")
    suspend fun getEtag(@Query("_") cacheBust: Long): EtagResponse

    @GET("api/dashboard")
    suspend fun getDashboardRange(
        @Query("start_date") startDate: String,
        @Query("end_date") endDate: String,
        @Query("_") cacheBust: Long,
    ): DashboardRangeResponse

    @GET("api/mobile/tasks")
    suspend fun getTasks(
        @Query("start") start: String,
        @Query("end") end: String,
        @Query("_") cacheBust: Long,
    ): List<MobileTaskDto>

    @POST("api/tasks/{id}/complete")
    suspend fun completeTask(@Path("id") taskId: String): Response<Unit>

    @POST("api/auth/login")
    suspend fun login(@Body body: Map<String, String>): LoginResponse

    @GET("api/app/users")
    suspend fun getAppUsers(): List<AppUserDto>

    @GET("api/app/dashboard-upgrade")
    suspend fun getDashboardUpgrade(): DashboardUpgradeResponse

    data class DashboardUpgradeResponse(
        val version: Int,
        val uploaded_at: String?,
    )

    data class EtagResponse(val etag: String)

    data class AppUserDto(val id: Int, val name: String)

    data class LoginResponse(val token: String, val person_id: Int, val name: String)

    data class MobileTaskDto(
        val id: String,
        val title: String,
        val description: String?,
        val icon: String?,
        val person_id: Int?,
        val date: String,
        val completed: Boolean,
    )

    data class DashboardRangeResponse(
        val weeks: List<DashboardWeekDto>? = null,
        val weekDays: List<WeekDay>? = null,
        val calendar: List<PersonCalendar>? = null,
    )

    data class DashboardWeekDto(
        val week_start: String,
        val weekDays: List<WeekDay>,
        val calendar: List<PersonCalendar>,
    )
}
